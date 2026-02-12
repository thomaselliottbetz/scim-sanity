"""Tests for the HTTP client (SCIMClient) against the mock SCIM server.

Covers CRUD operations, auth modes (basic, bearer), Content-Type headers,
429 retry behavior, custom timeouts, and secret redaction.
"""

import pytest
from scim_sanity.http_client import SCIMClient, redact_auth
from tests.mock_scim_server import MockSCIMServer


@pytest.fixture
def server():
    with MockSCIMServer() as s:
        yield s


@pytest.fixture
def client(server):
    return SCIMClient(server.base_url)


def test_get_service_provider_config(client):
    resp = client.get("/ServiceProviderConfig")
    assert resp.status_code == 200
    data = resp.json()
    assert "patch" in data


def test_post_and_get_user(client):
    payload = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "test@example.com",
    }
    resp = client.post("/Users", payload)
    assert resp.status_code == 201
    created = resp.json()
    assert "id" in created
    assert "meta" in created

    # GET it back
    resp2 = client.get(f"/Users/{created['id']}")
    assert resp2.status_code == 200
    assert resp2.json()["userName"] == "test@example.com"


def test_put_user(client):
    payload = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "put@example.com",
    }
    resp = client.post("/Users", payload)
    uid = resp.json()["id"]

    updated = dict(payload)
    updated["displayName"] = "Updated Name"
    resp2 = client.put(f"/Users/{uid}", updated)
    assert resp2.status_code == 200
    assert resp2.json()["displayName"] == "Updated Name"


def test_patch_user(client):
    payload = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "patch@example.com",
        "active": True,
    }
    resp = client.post("/Users", payload)
    uid = resp.json()["id"]

    patch = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": [{"op": "replace", "path": "active", "value": False}],
    }
    resp2 = client.patch(f"/Users/{uid}", patch)
    assert resp2.status_code == 200
    assert resp2.json()["active"] is False


def test_delete_user(client):
    payload = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": "delete@example.com",
    }
    resp = client.post("/Users", payload)
    uid = resp.json()["id"]

    resp2 = client.delete(f"/Users/{uid}")
    assert resp2.status_code == 204

    resp3 = client.get(f"/Users/{uid}")
    assert resp3.status_code == 404


def test_get_nonexistent_returns_404(client):
    resp = client.get("/Users/nonexistent")
    assert resp.status_code == 404


def test_content_type_header(client):
    resp = client.get("/ServiceProviderConfig")
    ct = resp.header("Content-Type")
    assert ct is not None
    assert "scim+json" in ct


def test_basic_auth():
    with MockSCIMServer() as server:
        client = SCIMClient(server.base_url, username="admin", password="secret")
        resp = client.get("/ServiceProviderConfig")
        assert resp.status_code == 200


def test_bearer_auth():
    with MockSCIMServer() as server:
        client = SCIMClient(server.base_url, token="test-token")
        resp = client.get("/ServiceProviderConfig")
        assert resp.status_code == 200


def test_429_retry():
    """Client should automatically retry on 429 with Retry-After."""
    with MockSCIMServer(non_conformances={"throttle_count": 2}) as server:
        client = SCIMClient(server.base_url)
        resp = client.get("/ServiceProviderConfig")
        # After 2 retries it should succeed
        assert resp.status_code == 200


def test_custom_timeout():
    with MockSCIMServer() as server:
        client = SCIMClient(server.base_url, timeout=5)
        resp = client.get("/ServiceProviderConfig")
        assert resp.status_code == 200


def test_redact_auth():
    headers = {
        "Authorization": "Bearer secret-token-123",
        "Content-Type": "application/scim+json",
    }
    redacted = redact_auth(headers)
    assert redacted["Authorization"] == "***REDACTED***"
    assert redacted["Content-Type"] == "application/scim+json"
    # Original should not be mutated
    assert headers["Authorization"] == "Bearer secret-token-123"
