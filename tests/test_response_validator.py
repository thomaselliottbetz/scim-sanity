"""Tests for the server response validator (ServerResponseValidator).

Covers resource response validation, strict vs compat modes, ListResponse
and error response validation, DELETE response checks, and ETag/meta.version
consistency.  Uses hand-crafted response dicts — no mock server needed.
"""

import pytest
from scim_sanity.response_validator import ServerResponseValidator, WARN, FAIL


@pytest.fixture
def rv():
    """Strict-mode validator."""
    return ServerResponseValidator(strict=True)


@pytest.fixture
def rv_compat():
    """Compat-mode validator."""
    return ServerResponseValidator(strict=False)


class TestResourceResponse:

    def test_valid_user_response(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "abc123",
            "userName": "test@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2024-01-01T00:00:00Z",
                "lastModified": "2024-01-01T00:00:00Z",
                "location": "https://example.com/scim/v2/Users/abc123",
            },
        }
        ok, errors = rv.validate_resource_response(
            data, expected_status=200, actual_status=200,
            headers={"Content-Type": "application/scim+json"},
            resource_type="User",
        )
        assert ok, f"Expected valid, got errors: {errors}"

    def test_missing_id(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "userName": "test@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2024-01-01T00:00:00Z",
                "lastModified": "2024-01-01T00:00:00Z",
            },
        }
        ok, errors = rv.validate_resource_response(
            data, expected_status=200, actual_status=200,
        )
        assert not ok
        assert any("'id'" in str(e) for e in errors)

    def test_missing_meta(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "abc123",
            "userName": "test@example.com",
        }
        ok, errors = rv.validate_resource_response(
            data, expected_status=200, actual_status=200,
        )
        assert not ok
        assert any("'meta'" in str(e) for e in errors)

    def test_missing_meta_fields(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "abc123",
            "userName": "test@example.com",
            "meta": {},
        }
        ok, errors = rv.validate_resource_response(
            data, expected_status=200, actual_status=200,
        )
        assert not ok
        assert any("resourceType" in str(e) for e in errors)
        assert any("created" in str(e) for e in errors)
        assert any("lastModified" in str(e) for e in errors)

    def test_password_in_response(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "abc123",
            "userName": "test@example.com",
            "password": "should-not-be-here",
            "meta": {
                "resourceType": "User",
                "created": "2024-01-01T00:00:00Z",
                "lastModified": "2024-01-01T00:00:00Z",
            },
        }
        ok, errors = rv.validate_resource_response(
            data, expected_status=200, actual_status=200,
        )
        assert not ok
        assert any("password" in str(e).lower() for e in errors)

    def test_wrong_status_code(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "abc123",
            "userName": "test@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2024-01-01T00:00:00Z",
                "lastModified": "2024-01-01T00:00:00Z",
            },
        }
        ok, errors = rv.validate_resource_response(
            data, expected_status=201, actual_status=200,
        )
        assert not ok
        assert any("201" in str(e) for e in errors)

    def test_wrong_content_type(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "abc123",
            "userName": "test@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2024-01-01T00:00:00Z",
                "lastModified": "2024-01-01T00:00:00Z",
            },
        }
        ok, errors = rv.validate_resource_response(
            data, expected_status=200, actual_status=200,
            headers={"Content-Type": "text/html"},
        )
        assert not ok
        assert any("Content-Type" in str(e) for e in errors)

    def test_location_mismatch_on_201(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "abc123",
            "userName": "test@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2024-01-01T00:00:00Z",
                "lastModified": "2024-01-01T00:00:00Z",
                "location": "https://example.com/scim/v2/Users/abc123",
            },
        }
        ok, errors = rv.validate_resource_response(
            data, expected_status=201, actual_status=201,
            headers={
                "Content-Type": "application/scim+json",
                "Location": "https://wrong.example.com/Users/abc123",
            },
        )
        assert not ok
        assert any("Location" in str(e) for e in errors)

    def test_resource_type_mismatch(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "abc123",
            "userName": "test@example.com",
            "meta": {
                "resourceType": "Group",
                "created": "2024-01-01T00:00:00Z",
                "lastModified": "2024-01-01T00:00:00Z",
            },
        }
        ok, errors = rv.validate_resource_response(
            data, expected_status=200, actual_status=200,
            resource_type="User",
        )
        assert not ok
        assert any("resourceType" in str(e) for e in errors)


class TestStrictVsCompat:

    def test_application_json_strict_warns(self, rv):
        """In strict mode, application/json produces WARN-severity errors."""
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "abc123",
            "userName": "test@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2024-01-01T00:00:00Z",
                "lastModified": "2024-01-01T00:00:00Z",
            },
        }
        ok, errors = rv.validate_resource_response(
            data, expected_status=200, actual_status=200,
            headers={"Content-Type": "application/json"},
        )
        # strict: application/json triggers a WARN-severity error (is_strict_only=True)
        # but _is_valid only checks for FAIL severity, so ok should still be True
        # Wait - in strict mode, _sev(is_strict_only=True) returns FAIL
        assert not ok
        ct_errs = [e for e in errors if "Content-Type" in str(e)]
        assert len(ct_errs) > 0

    def test_application_json_compat_passes(self, rv_compat):
        """In compat mode, application/json produces warnings but is_valid=True."""
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "abc123",
            "userName": "test@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2024-01-01T00:00:00Z",
                "lastModified": "2024-01-01T00:00:00Z",
            },
        }
        ok, errors = rv_compat.validate_resource_response(
            data, expected_status=200, actual_status=200,
            headers={"Content-Type": "application/json"},
        )
        assert ok, f"Expected valid in compat mode, got errors: {errors}"
        ct_warns = [e for e in errors if e.severity == WARN]
        assert len(ct_warns) > 0

    def test_error_response_compat_missing_schema(self, rv_compat):
        """In compat mode, missing error schema is a warning, not a failure."""
        data = {"status": "400", "detail": "Bad request"}
        ok, errors = rv_compat.validate_error_response(data, 400, 400)
        assert ok, "Expected valid in compat mode"
        warns = [e for e in errors if e.severity == WARN]
        assert len(warns) > 0

    def test_error_response_strict_missing_schema(self, rv):
        """In strict mode, missing error schema is a failure."""
        data = {"status": "400", "detail": "Bad request"}
        ok, errors = rv.validate_error_response(data, 400, 400)
        assert not ok

    def test_location_mismatch_compat_is_warning(self, rv_compat):
        """In compat mode, Location header mismatch is a warning."""
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "abc123",
            "userName": "test@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2024-01-01T00:00:00Z",
                "lastModified": "2024-01-01T00:00:00Z",
                "location": "https://example.com/Users/abc123",
            },
        }
        ok, errors = rv_compat.validate_resource_response(
            data, expected_status=201, actual_status=201,
            headers={
                "Content-Type": "application/scim+json",
                "Location": "https://wrong.example.com/Users/abc123",
            },
        )
        assert ok, "Expected valid in compat mode"
        warns = [e for e in errors if e.severity == WARN]
        assert any("Location" in str(w) for w in warns)


class TestListResponse:

    def test_valid_list_response(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 1,
            "Resources": [{"id": "abc"}],
        }
        ok, errors = rv.validate_list_response(data, 200)
        assert ok, f"Expected valid, got errors: {errors}"

    def test_missing_list_schema(self, rv):
        data = {
            "totalResults": 1,
            "schemas": [],
            "Resources": [],
        }
        ok, errors = rv.validate_list_response(data, 200)
        assert not ok

    def test_missing_total_results(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "Resources": [],
        }
        ok, errors = rv.validate_list_response(data, 200)
        assert not ok


class TestErrorResponse:

    def test_valid_error_response(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "404",
            "detail": "Resource not found",
        }
        ok, errors = rv.validate_error_response(data, 404, 404)
        assert ok

    def test_missing_error_schema(self, rv):
        data = {"status": "400", "detail": "Bad request"}
        ok, errors = rv.validate_error_response(data, 400, 400)
        assert not ok

    def test_missing_status_field(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "detail": "Not found",
        }
        ok, errors = rv.validate_error_response(data, 404, 404)
        assert not ok


class TestDeleteResponse:

    def test_valid_delete(self, rv):
        ok, errors = rv.validate_delete_response(204)
        assert ok

    def test_wrong_delete_status(self, rv):
        ok, errors = rv.validate_delete_response(200)
        assert not ok

    def test_delete_with_body_strict(self, rv):
        """Strict mode: 204 with body is a failure."""
        ok, errors = rv.validate_delete_response(204, body='{"detail":"deleted"}')
        assert not ok

    def test_delete_with_body_compat(self, rv_compat):
        """Compat mode: 204 with body is a warning."""
        ok, errors = rv_compat.validate_delete_response(204, body='{"detail":"deleted"}')
        assert ok
        warns = [e for e in errors if e.severity == WARN]
        assert len(warns) > 0


class TestETagConsistency:

    def test_etag_matches_version(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "abc123",
            "userName": "test@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2024-01-01T00:00:00Z",
                "lastModified": "2024-01-01T00:00:00Z",
                "version": 'W/"abc12345"',
            },
        }
        ok, errors = rv.validate_resource_response(
            data, expected_status=200, actual_status=200,
            headers={
                "Content-Type": "application/scim+json",
                "ETag": 'W/"abc12345"',
            },
        )
        assert ok, f"Expected valid, got errors: {errors}"

    def test_etag_mismatch_strict(self, rv):
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "abc123",
            "userName": "test@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2024-01-01T00:00:00Z",
                "lastModified": "2024-01-01T00:00:00Z",
                "version": 'W/"version1"',
            },
        }
        ok, errors = rv.validate_resource_response(
            data, expected_status=200, actual_status=200,
            headers={
                "Content-Type": "application/scim+json",
                "ETag": 'W/"differentversion"',
            },
        )
        assert not ok
        assert any("ETag" in str(e) for e in errors)

    def test_etag_mismatch_compat(self, rv_compat):
        data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "abc123",
            "userName": "test@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2024-01-01T00:00:00Z",
                "lastModified": "2024-01-01T00:00:00Z",
                "version": 'W/"version1"',
            },
        }
        ok, errors = rv_compat.validate_resource_response(
            data, expected_status=200, actual_status=200,
            headers={
                "Content-Type": "application/scim+json",
                "ETag": 'W/"differentversion"',
            },
        )
        assert ok  # compat: warning, not failure
        warns = [e for e in errors if e.severity == WARN]
        assert any("ETag" in str(w) for w in warns)
