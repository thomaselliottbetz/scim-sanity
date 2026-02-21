"""Validates SCIM server responses — the inverse of validator.py.

Client-side validation (validator.py) ensures payloads *sent to* a server are correct.
This module validates what the server *sends back*: responses MUST include ``id`` and
``meta``, MUST NOT include writeOnly attributes like ``password``, and must use correct
status codes, Content-Type headers, and ETag consistency.

Two validation modes are supported:

- **Strict** (default): All RFC 7643/7644 deviations are reported as FAIL errors.
- **Compat**: Known real-world deviations (e.g., ``application/json`` instead of
  ``application/scim+json``, DELETE 204 with body, missing error schema) are
  reported as WARN warnings that don't cause overall validation failure.

The mode is controlled by ``ServerResponseValidator(strict=True|False)`` and the
``_sev(is_strict_only)`` helper determines the severity for each check.
"""

from typing import Any, Dict, List, Optional, Tuple

from .schemas import get_schema


# Severity constants used by ServerValidationError and ProbeResult
FAIL = "fail"
WARN = "warn"


class ServerValidationError:
    """A single validation finding from checking a server response.

    Attributes:
        message:   Human-readable description of the issue.
        path:      Dot-notation path to the problematic field (e.g. ``meta.resourceType``).
        severity:  ``FAIL`` for spec violations, ``WARN`` for known deviations in compat mode.
    """

    def __init__(self, message: str, path: str = "", severity: str = FAIL):
        self.message = message
        self.path = path
        self.severity = severity

    def __str__(self):
        loc = f" at {self.path}" if self.path else ""
        prefix = "[WARN] " if self.severity == WARN else ""
        return f"{prefix}{self.message}{loc}"

    def __repr__(self):
        return f"ServerValidationError({self.message!r}, path={self.path!r}, severity={self.severity!r})"


class ServerResponseValidator:
    """Validates SCIM server responses for RFC 7643/7644 conformance.

    Returns ``(is_valid, errors)`` tuples from each validate method.
    In compat mode (``strict=False``), only FAIL-severity errors cause
    ``is_valid=False``; WARN-severity errors are informational.

    Args:
        strict: If True, all deviations are FAIL.  If False, known real-world
                deviations are downgraded to WARN.
    """

    def __init__(self, strict: bool = True):
        self.strict = strict

    def _sev(self, is_strict_only: bool = False) -> str:
        """Determine error severity based on validation mode.

        Args:
            is_strict_only: If True, this check represents a known real-world
                deviation that should be WARN in compat mode but FAIL in strict mode.
                If False, the deviation is always FAIL regardless of mode.

        Returns:
            ``FAIL`` or ``WARN`` severity constant.
        """
        if is_strict_only and not self.strict:
            return WARN
        return FAIL

    # -- Resource response validation ----------------------------------------

    def validate_resource_response(
        self,
        data: Dict[str, Any],
        expected_status: int,
        actual_status: int,
        headers: Optional[Dict[str, str]] = None,
        resource_type: Optional[str] = None,
    ) -> Tuple[bool, List[ServerValidationError]]:
        """Validate a server response containing a single SCIM resource.

        Checks status code, Content-Type, ``schemas`` array, ``id`` and ``meta``
        presence, writeOnly attribute absence, Location header on 201, and
        ETag/meta.version consistency.

        Returns:
            ``(is_valid, list_of_errors)`` — in compat mode, warnings don't
            cause ``is_valid=False``.
        """
        errors: List[ServerValidationError] = []

        # Status code — always a hard failure if wrong
        if actual_status != expected_status:
            errors.append(ServerValidationError(
                f"Expected HTTP {expected_status}, got {actual_status}"
            ))
            # If the server returned an error status, skip SCIM field validation —
            # missing id/meta/schemas are predictable consequences of the error,
            # not independent conformance issues worth reporting separately
            if actual_status >= 400:
                return self._is_valid(errors), errors

        if data is None:
            if expected_status != 204:
                errors.append(ServerValidationError("Response body is empty"))
            return self._is_valid(errors), errors

        # Content-Type: application/scim+json is required by spec,
        # but many servers use application/json (compat: warn only)
        if headers:
            ct = _header_value(headers, "Content-Type")
            if ct:
                if "application/scim+json" in ct:
                    pass  # correct per spec
                elif "application/json" in ct:
                    errors.append(ServerValidationError(
                        f"Content-Type should be application/scim+json, got '{ct}'",
                        severity=self._sev(is_strict_only=True),
                    ))
                else:
                    errors.append(ServerValidationError(
                        f"Content-Type should be application/scim+json, got '{ct}'"
                    ))

        # schemas array — required by RFC 7643 Section 3
        schemas = data.get("schemas")
        if not schemas or not isinstance(schemas, list):
            errors.append(ServerValidationError("Response missing 'schemas' array"))
            return False, errors

        # id — server MUST assign and return (RFC 7643 Section 3.1)
        if "id" not in data:
            errors.append(ServerValidationError(
                "Server response missing required attribute 'id'"
            ))

        # meta — server MUST return with resourceType, created, lastModified
        meta = data.get("meta")
        if meta is None:
            errors.append(ServerValidationError(
                "Server response missing required attribute 'meta'"
            ))
        elif isinstance(meta, dict):
            for field in ("resourceType", "created", "lastModified"):
                if field not in meta:
                    errors.append(ServerValidationError(
                        f"meta.{field} must be present in server response",
                        path=f"meta.{field}",
                    ))

            # meta.version type check (should be a weak ETag string like W/"abc")
            version = meta.get("version")
            if version is not None and not isinstance(version, str):
                errors.append(ServerValidationError(
                    f"meta.version must be a string, got {type(version).__name__}",
                    path="meta.version",
                ))

        # ETag header consistency with meta.version (RFC 7644 Section 3.14)
        # When both are present, they should match
        if headers and meta and isinstance(meta, dict):
            etag = _header_value(headers, "ETag")
            version = meta.get("version")
            if etag and version and etag.strip('"') != version.strip('"'):
                errors.append(ServerValidationError(
                    f"ETag header '{etag}' does not match meta.version '{version}'",
                    severity=self._sev(is_strict_only=True),
                ))

        # Location header on 201 Created — must match meta.location
        if actual_status == 201 and headers and meta and isinstance(meta, dict):
            loc_header = _header_value(headers, "Location")
            meta_loc = meta.get("location")
            if loc_header and meta_loc and loc_header != meta_loc:
                errors.append(ServerValidationError(
                    f"Location header '{loc_header}' does not match meta.location '{meta_loc}'",
                    severity=self._sev(is_strict_only=True),
                ))
            elif not loc_header and actual_status == 201:
                errors.append(ServerValidationError(
                    "Location header should be present on 201 Created",
                    severity=self._sev(is_strict_only=True),
                ))

        # writeOnly attributes (e.g., password) must never appear in responses
        self._check_write_only(data, schemas, errors)

        # Verify meta.resourceType matches what we expect
        if resource_type:
            self._check_resource_type_match(data, resource_type, errors)

        return self._is_valid(errors), errors

    # -- ListResponse validation ---------------------------------------------

    def validate_list_response(
        self,
        data: Dict[str, Any],
        actual_status: int,
        headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, List[ServerValidationError]]:
        """Validate a ListResponse from the server (RFC 7644 Section 3.4.2)."""
        errors: List[ServerValidationError] = []

        if actual_status != 200:
            errors.append(ServerValidationError(
                f"Expected HTTP 200 for list, got {actual_status}"
            ))

        if data is None:
            errors.append(ServerValidationError("Response body is empty"))
            return False, errors

        # Must include the ListResponse schema URN
        schemas = data.get("schemas", [])
        if "urn:ietf:params:scim:api:messages:2.0:ListResponse" not in schemas:
            errors.append(ServerValidationError(
                "ListResponse must include schema 'urn:ietf:params:scim:api:messages:2.0:ListResponse'"
            ))

        # totalResults is required
        if "totalResults" not in data:
            errors.append(ServerValidationError(
                "ListResponse missing required attribute 'totalResults'"
            ))
        elif not isinstance(data["totalResults"], int):
            errors.append(ServerValidationError(
                f"totalResults must be an integer, got {type(data['totalResults']).__name__}",
                severity=self._sev(is_strict_only=True),
            ))

        # Resources must be an array if present
        if "Resources" in data and not isinstance(data["Resources"], list):
            errors.append(ServerValidationError(
                "'Resources' must be an array"
            ))

        # Pagination fields must be integers if present
        for field in ("startIndex", "itemsPerPage"):
            if field in data and not isinstance(data[field], int):
                errors.append(ServerValidationError(
                    f"'{field}' must be an integer",
                    severity=self._sev(is_strict_only=True),
                ))

        return self._is_valid(errors), errors

    # -- Error response validation -------------------------------------------

    def validate_error_response(
        self,
        data: Dict[str, Any],
        expected_status: int,
        actual_status: int,
    ) -> Tuple[bool, List[ServerValidationError]]:
        """Validate a SCIM error response (RFC 7644 Section 3.12)."""
        errors: List[ServerValidationError] = []

        if actual_status != expected_status:
            errors.append(ServerValidationError(
                f"Expected HTTP {expected_status}, got {actual_status}"
            ))

        if data is None:
            # Some servers return empty body on errors — compat: warn only
            errors.append(ServerValidationError(
                "Error response body is empty",
                severity=self._sev(is_strict_only=True),
            ))
            return self._is_valid(errors), errors

        # Error schema URN is required per spec but often missing in practice
        schemas = data.get("schemas", [])
        if "urn:ietf:params:scim:api:messages:2.0:Error" not in schemas:
            errors.append(ServerValidationError(
                "Error response must include schema 'urn:ietf:params:scim:api:messages:2.0:Error'",
                severity=self._sev(is_strict_only=True),
            ))

        # status field is required in the error body
        if "status" not in data:
            errors.append(ServerValidationError(
                "Error response missing required attribute 'status'",
                severity=self._sev(is_strict_only=True),
            ))

        return self._is_valid(errors), errors

    # -- DELETE response validation ------------------------------------------

    def validate_delete_response(
        self,
        actual_status: int,
        body: str = "",
    ) -> Tuple[bool, List[ServerValidationError]]:
        """Validate a DELETE response (RFC 7644 Section 3.6 — expect 204 No Content)."""
        errors: List[ServerValidationError] = []
        if actual_status != 204:
            errors.append(ServerValidationError(
                f"Expected HTTP 204 for DELETE, got {actual_status}"
            ))
        # Some servers return a body on 204 — technically wrong, but common
        if body and body.strip():
            errors.append(ServerValidationError(
                "DELETE 204 response should have no body",
                severity=self._sev(is_strict_only=True),
            ))
        return self._is_valid(errors), errors

    # -- Internals -----------------------------------------------------------

    def _is_valid(self, errors: List[ServerValidationError]) -> bool:
        """Determine overall validity.  Only FAIL-severity errors count."""
        return not any(e.severity == FAIL for e in errors)

    def _check_write_only(
        self,
        data: Dict[str, Any],
        schemas: List[str],
        errors: List[ServerValidationError],
    ):
        """Verify that writeOnly/returned-never attributes are absent from the response.

        Per RFC 7643 Section 7, attributes with ``returned: never`` (e.g., ``password``)
        must never appear in any server response.
        """
        for schema_urn in schemas:
            schema = get_schema(schema_urn)
            if not schema:
                continue
            # Extension schemas store their data under the schema URN key
            is_extension = schema_urn.startswith("urn:ietf:params:scim:schemas:extension:")
            check_data = data.get(schema_urn, {}) if is_extension else data
            if not isinstance(check_data, dict):
                continue
            for attr_def in schema.get("attributes", []):
                if attr_def.get("returned") == "never" or attr_def.get("mutability") == "writeOnly":
                    attr_name = attr_def["name"]
                    if attr_name in check_data:
                        errors.append(ServerValidationError(
                            f"writeOnly attribute '{attr_name}' must not appear in server response",
                            path=attr_name,
                        ))

    def _check_resource_type_match(
        self,
        data: Dict[str, Any],
        expected_type: str,
        errors: List[ServerValidationError],
    ):
        """Verify that ``meta.resourceType`` matches the expected resource type."""
        meta = data.get("meta", {})
        if isinstance(meta, dict):
            rt = meta.get("resourceType")
            if rt and rt != expected_type:
                errors.append(ServerValidationError(
                    f"meta.resourceType '{rt}' does not match expected '{expected_type}'",
                    path="meta.resourceType",
                ))


def _header_value(headers: Dict[str, str], name: str) -> Optional[str]:
    """Case-insensitive HTTP header lookup."""
    lower = name.lower()
    for k, v in headers.items():
        if k.lower() == lower:
            return v
    return None
