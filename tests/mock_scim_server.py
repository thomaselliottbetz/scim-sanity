"""Mock SCIM server for testing the probe harness.

Runs an in-memory SCIM server using ``http.server`` from stdlib in a
background thread.  Supports User, Group, Agent, AgenticApplication CRUD
with configurable non-conformances to verify that the probe correctly
detects real-world server pathologies.

Non-conformance flags (pass via ``non_conformances`` dict):

  ``missing_id``           — Omit ``id`` from resource responses.
  ``missing_meta``         — Omit ``meta`` from resource responses.
  ``missing_meta_fields``  — Include ``meta`` but omit ``created``/``lastModified``.
  ``password_in_response`` — Echo ``password`` back in response body
                             (violates RFC 7643 ``returned: never``).
  ``throttle_count``       — Return 429 for the first N requests, with
                             ``Retry-After: 0`` header.
  ``stale_after_put``      — First GET after a PUT returns stale (pre-PUT)
                             data, simulating eventual consistency.
  ``reject_filters``       — Respond 400 to any request with a ``filter=``
                             query parameter.
  ``content_type_json``    — Use ``application/json`` instead of
                             ``application/scim+json`` in responses.

Usage::

    with MockSCIMServer(non_conformances={"missing_meta": True}) as server:
        client = SCIMClient(server.base_url)
        resp = client.get("/Users")
"""

import json
import threading
import uuid
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, Optional


class MockSCIMHandler(BaseHTTPRequestHandler):
    """Handles SCIM HTTP requests against in-memory dict storage.

    Server state (stores, non_conformances, stale_snapshots) is stored on
    the ``HTTPServer`` instance, which is shared across all handler instances.
    """

    def log_message(self, format, *args):
        """Suppress request logging during tests to keep output clean."""
        pass

    # -- Throttle gate -------------------------------------------------------

    def _throttle_check(self) -> bool:
        """Return 429 if ``throttle_count > 0`` and decrement.  Returns True if throttled."""
        tc = self.server.non_conformances.get("throttle_count", 0)
        if tc > 0:
            self.server.non_conformances["throttle_count"] = tc - 1
            self.send_response(429)
            self.send_header("Retry-After", "0")
            self.send_header("Content-Type", "application/scim+json")
            body = json.dumps({
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
                "status": "429",
                "detail": "Too Many Requests",
            }).encode()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return True
        return False

    # -- Response helpers ----------------------------------------------------

    def _content_type(self) -> str:
        """Return the Content-Type to use, respecting ``content_type_json`` flag."""
        if self.server.non_conformances.get("content_type_json"):
            return "application/json"
        return "application/scim+json"

    def _send_json(self, status: int, body: Any, extra_headers: Optional[Dict[str, str]] = None):
        """Send a JSON response with appropriate Content-Type and headers."""
        self.send_response(status)
        self.send_header("Content-Type", self._content_type())
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        payload = json.dumps(body).encode("utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_error(self, status: int, detail: str = ""):
        """Send a SCIM error response with proper schema and status field."""
        body = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": str(status),
            "detail": detail,
        }
        self._send_json(status, body)

    def _read_body(self) -> Optional[dict]:
        """Read and parse the request body as JSON.  Returns None if empty or invalid."""
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    # -- URL parsing ---------------------------------------------------------

    def _parse_path(self):
        """Extract ``(resource_type, resource_id)`` from the URL path.

        Examples:
          ``/Users``        -> ``("Users", None)``
          ``/Users/abc123`` -> ``("Users", "abc123")``
        """
        path = self.path.split("?")[0].rstrip("/")
        prefix = self.server.base_path.rstrip("/")
        if prefix and path.startswith(prefix):
            path = path[len(prefix):]

        parts = [p for p in path.split("/") if p]
        if len(parts) == 0:
            return None, None
        if len(parts) == 1:
            return parts[0], None
        return parts[0], parts[1]

    def _get_store(self, resource_type: str) -> Optional[dict]:
        """Look up the in-memory store for a resource type endpoint."""
        return self.server.stores.get(resource_type)

    # -- Server-managed field generation -------------------------------------

    def _make_meta(self, resource_type: str, resource_id: str) -> dict:
        """Generate a ``meta`` object with resourceType, timestamps, location, and version."""
        now = datetime.now(timezone.utc).isoformat()
        location = f"{self.server.base_url}/{resource_type}/{resource_id}"
        meta = {
            "resourceType": _resource_type_name(resource_type),
            "created": now,
            "lastModified": now,
            "location": location,
            "version": f'W/"{resource_id[:8]}"',
        }
        if self.server.non_conformances.get("missing_meta_fields"):
            meta.pop("created", None)
            meta.pop("lastModified", None)
        return meta

    def _enrich_response(self, resource_type: str, resource_id: str, data: dict) -> dict:
        """Add server-managed fields (id, meta) to a resource before returning it.

        Applies non-conformance flags: ``missing_id``, ``missing_meta``,
        ``password_in_response``.
        """
        result = dict(data)
        result["id"] = resource_id
        if self.server.non_conformances.get("missing_id"):
            result.pop("id", None)

        if not self.server.non_conformances.get("missing_meta"):
            result["meta"] = self._make_meta(resource_type, resource_id)

        # password must never be returned per RFC 7643 (returned: never),
        # unless we're deliberately simulating that non-conformance
        if self.server.non_conformances.get("password_in_response") and "password" in data:
            result["password"] = data["password"]
        else:
            result.pop("password", None)

        return result

    def _has_filter_query(self) -> bool:
        """Check if the request URL contains a ``filter=`` query parameter."""
        return "filter=" in self.path

    # -- HTTP method handlers ------------------------------------------------

    def do_GET(self):
        """Handle GET requests for discovery, list, and single-resource retrieval."""
        if self._throttle_check():
            return

        resource_type, resource_id = self._parse_path()

        # Discovery endpoints — return static config responses
        if resource_type == "ServiceProviderConfig":
            return self._send_json(200, self.server.service_provider_config)
        if resource_type == "Schemas":
            return self._send_json(200, self.server.schemas_response)
        if resource_type == "ResourceTypes":
            return self._send_json(200, self.server.resource_types_response)

        store = self._get_store(resource_type)
        if store is None:
            return self._send_error(404, f"Unknown resource type: {resource_type}")

        if resource_id is None:
            # List operation — return all resources as a ListResponse
            if self.server.non_conformances.get("reject_filters") and self._has_filter_query():
                return self._send_error(400, "Filtering is not supported")

            resources = []
            for rid, data in store.items():
                resources.append(self._enrich_response(resource_type, rid, data))
            list_resp = {
                "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
                "totalResults": len(resources),
                "Resources": resources,
                "startIndex": 1,
                "itemsPerPage": len(resources),
            }
            return self._send_json(200, list_resp)
        else:
            # Single resource retrieval
            if resource_id not in store:
                return self._send_error(404, "Resource not found")

            # Eventual consistency simulation: return stale data once after PUT
            stale_key = f"_stale_{resource_type}_{resource_id}"
            stale_data = self.server.stale_snapshots.get(stale_key)
            if stale_data is not None:
                del self.server.stale_snapshots[stale_key]
                enriched = self._enrich_response(resource_type, resource_id, stale_data)
                return self._send_json(200, enriched)

            enriched = self._enrich_response(resource_type, resource_id, store[resource_id])
            return self._send_json(200, enriched)

    def do_POST(self):
        """Handle POST requests to create new resources."""
        if self._throttle_check():
            return

        resource_type, _ = self._parse_path()
        store = self._get_store(resource_type)
        if store is None:
            return self._send_error(404, f"Unknown resource type: {resource_type}")

        body = self._read_body()
        if body is None:
            return self._send_error(400, "Invalid or missing JSON body")

        # Validate schemas array
        schemas = body.get("schemas")
        if not schemas or not isinstance(schemas, list):
            return self._send_error(400, "Missing or invalid 'schemas' field")

        # Validate required attributes per resource type
        rtype = _resource_type_name(resource_type)
        if rtype == "User" and "userName" not in body:
            return self._send_error(400, "Missing required attribute: userName")
        if rtype == "Group" and "displayName" not in body:
            return self._send_error(400, "Missing required attribute: displayName")
        if rtype in ("Agent", "AgenticApplication") and "name" not in body:
            return self._send_error(400, "Missing required attribute: name")

        # Assign server-generated id and store
        resource_id = uuid.uuid4().hex
        store[resource_id] = body
        enriched = self._enrich_response(resource_type, resource_id, body)

        # Return 201 with Location and ETag headers
        location = f"{self.server.base_url}/{resource_type}/{resource_id}"
        etag = enriched.get("meta", {}).get("version", "")
        extra = {"Location": location}
        if etag:
            extra["ETag"] = etag
        self._send_json(201, enriched, extra_headers=extra)

    def do_PUT(self):
        """Handle PUT requests to replace a resource."""
        if self._throttle_check():
            return

        resource_type, resource_id = self._parse_path()
        store = self._get_store(resource_type)
        if store is None or resource_id is None:
            return self._send_error(404, "Resource not found")
        if resource_id not in store:
            return self._send_error(404, "Resource not found")

        body = self._read_body()
        if body is None:
            return self._send_error(400, "Invalid or missing JSON body")

        # Eventual consistency simulation: save pre-update snapshot
        if self.server.non_conformances.get("stale_after_put"):
            stale_key = f"_stale_{resource_type}_{resource_id}"
            self.server.stale_snapshots[stale_key] = dict(store[resource_id])

        store[resource_id] = body
        enriched = self._enrich_response(resource_type, resource_id, body)
        self._send_json(200, enriched)

    def do_PATCH(self):
        """Handle PATCH requests to partially update a resource.

        Supports ``add``, ``replace``, and ``remove`` operations on
        top-level attributes.
        """
        if self._throttle_check():
            return

        resource_type, resource_id = self._parse_path()
        store = self._get_store(resource_type)
        if store is None or resource_id is None:
            return self._send_error(404, "Resource not found")
        if resource_id not in store:
            return self._send_error(404, "Resource not found")

        body = self._read_body()
        if body is None:
            return self._send_error(400, "Invalid or missing JSON body")

        # Apply each operation to the stored resource
        operations = body.get("Operations", [])
        resource = store[resource_id]
        for op in operations:
            op_type = op.get("op")
            path = op.get("path")
            value = op.get("value")
            if op_type in ("add", "replace") and path:
                resource[path] = value
            elif op_type == "remove" and path:
                resource.pop(path, None)

        store[resource_id] = resource
        enriched = self._enrich_response(resource_type, resource_id, resource)
        self._send_json(200, enriched)

    def do_DELETE(self):
        """Handle DELETE requests.  Returns 204 No Content on success."""
        if self._throttle_check():
            return

        resource_type, resource_id = self._parse_path()
        store = self._get_store(resource_type)
        if store is None or resource_id is None:
            return self._send_error(404, "Resource not found")
        if resource_id not in store:
            return self._send_error(404, "Resource not found")

        del store[resource_id]
        self.send_response(204)
        self.end_headers()


def _resource_type_name(endpoint: str) -> str:
    """Map a plural endpoint name (e.g. ``Users``) to the SCIM resourceType name (``User``)."""
    mapping = {
        "Users": "User",
        "Groups": "Group",
        "Agents": "Agent",
        "AgenticApplications": "AgenticApplication",
    }
    return mapping.get(endpoint, endpoint)


class MockSCIMServer:
    """Configurable in-memory SCIM server for testing.

    Runs in a background daemon thread.  Use as a context manager::

        with MockSCIMServer(non_conformances={"missing_meta": True}) as server:
            # server.base_url is available
            ...

    Args:
        port:                TCP port to listen on (0 = auto-assign).
        non_conformances:    Dict of non-conformance flags (see module docstring).
        supported_resources: List of resource type names to expose
                             (default: User, Group, Agent, AgenticApplication).
    """

    def __init__(self, port: int = 0, non_conformances: Optional[Dict[str, Any]] = None,
                 supported_resources: Optional[list] = None):
        self.non_conformances = dict(non_conformances or {})
        self.supported_resources = supported_resources or ["User", "Group", "Agent", "AgenticApplication"]

        self.server = HTTPServer(("127.0.0.1", port), MockSCIMHandler)
        actual_port = self.server.server_address[1]
        self.server.base_url = f"http://127.0.0.1:{actual_port}"
        self.server.base_path = ""
        self.server.non_conformances = self.non_conformances
        self.server.stale_snapshots = {}  # keyed by "_stale_{type}_{id}"

        # Create an in-memory store (dict) for each supported resource type
        self.server.stores = {}
        for rt in self.supported_resources:
            endpoint = rt + "s"  # User -> Users, Group -> Groups, etc.
            self.server.stores[endpoint] = {}

        # Static discovery endpoint responses
        self.server.service_provider_config = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
            "patch": {"supported": True},
            "bulk": {"supported": False},
            "filter": {"supported": True, "maxResults": 200},
            "changePassword": {"supported": False},
            "sort": {"supported": False},
            "etag": {"supported": False},
            "authenticationSchemes": [{"type": "oauthbearertoken", "name": "Bearer"}],
        }

        resource_types = []
        for rt in self.supported_resources:
            resource_types.append({
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                "name": rt,
                "endpoint": f"/{rt}s",
                "schema": f"urn:ietf:params:scim:schemas:core:2.0:{rt}",
            })
        self.server.resource_types_response = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": len(resource_types),
            "Resources": resource_types,
        }

        self.server.schemas_response = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 0,
            "Resources": [],
        }

        self._thread = None

    @property
    def base_url(self) -> str:
        """The base URL of the running server (e.g. ``http://127.0.0.1:54321``)."""
        return self.server.base_url

    def start(self):
        """Start the server in a daemon thread."""
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        """Shut down the server and join the thread."""
        self.server.shutdown()
        if self._thread:
            self._thread.join(timeout=5)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
