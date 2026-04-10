"""FastAPI application wrapping the scim-sanity core library.

This is the API layer (Layer 2b) in the three-layer architecture:

    Layer 1 — Core library (validator, probe/runner, etc.)
    Layer 2b — This module: thin REST wrapper around the core library
    Layer 3 — React/Cloudscape frontend (web/)

No validation or probe logic lives here. All business logic stays in the core.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# web/dist/ sits two levels up from this file (scim_sanity/ → project root → web/dist/)
_WEB_DIST = Path(__file__).parent.parent / "web" / "dist"

from . import __version__
from .validator import SCIMValidator
from .probe.runner import run_probe_api

app = FastAPI(title="scim-sanity API", version=__version__)

# Serve pre-built JS/CSS bundles from web/dist/assets/ at /assets.
# Only mounted when the frontend has been built; safe to skip in CLI-only installs.
if (_WEB_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=_WEB_DIST / "assets"), name="assets")


class ValidateRequest(BaseModel):
    payload: Dict[str, Any]
    operation: str = "full"


class ProbeRequest(BaseModel):
    url: str
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    strict: bool = True
    resource: Optional[str] = None
    tls_no_verify: bool = False
    skip_cleanup: bool = False
    timeout: int = 30
    profile: Optional[str] = None
    extra_user_fields: Optional[Dict[str, Any]] = None
    user_domain: Optional[str] = None
    proxy: Optional[str] = None
    ca_bundle: Optional[str] = None


_VALIDATE_RESPONSE_EXAMPLE = {
    "valid": False,
    "errors": [
        {
            "message": "Missing required attribute: 'userName'",
            "path": "userName",
            "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
        },
        {
            "message": "Immutable attribute 'id' should not be set by client",
            "path": "id",
            "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
        },
    ],
}


@app.post(
    "/api/validate",
    responses={
        200: {
            "description": "Validation result with list of RFC conformance errors",
            "content": {"application/json": {"example": _VALIDATE_RESPONSE_EXAMPLE}},
        }
    },
)
def validate(req: ValidateRequest):
    """Validate a SCIM payload against RFC 7643/7644 rules."""
    validator = SCIMValidator()
    is_valid, errors = validator.validate(req.payload, req.operation)
    return {
        "valid": is_valid,
        "errors": [e.to_dict() for e in errors],
    }


_PROBE_RESPONSE_EXAMPLE = {
    "scim_sanity_version": __version__,
    "mode": "strict",
    "timestamp": "2026-04-05 09:15:00",
    "summary": {
        "total": 31,
        "passed": 14,
        "failed": 13,
        "warnings": 1,
        "skipped": 3,
        "errors": 0,
    },
    "issues": [
        {
            "priority": "P3",
            "title": "Missing meta timestamps on resource responses",
            "fix": "Include meta.created and meta.lastModified in all resource representations",
            "rationale": "Without meta.lastModified, incremental sync is impossible — clients must full-scan every cycle or risk missing updates.",
            "affected_tests": 2,
        },
        {
            "priority": "E1",
            "title": "PUT not supported — server returns 405 Method Not Allowed",
            "fix": "Support PUT /Users/<id> and PUT /Groups/<id>, or document the omission in ServiceProviderConfig",
            "rationale": "RFC 7644 §3.5.1 says servers SHOULD support PUT; clients that issue PUT will receive 405 and may halt provisioning.",
            "affected_tests": 2,
        },
    ],
    "results": [
        {
            "name": "GET /ServiceProviderConfig",
            "status": "pass",
            "phase": "Phase 1 — Discovery",
        },
        {
            "name": "POST /Users",
            "status": "fail",
            "message": "meta.created must be present in server response (RFC 7643 §3.1) at meta.created",
            "phase": "Phase 2 — User CRUD Lifecycle",
        },
    ],
}


@app.post(
    "/api/probe",
    responses={
        200: {
            "description": "Probe results with per-test status, summary counts, and prioritised Fix Summary",
            "content": {"application/json": {"example": _PROBE_RESPONSE_EXAMPLE}},
        }
    },
)
def probe(req: ProbeRequest):
    """Run a conformance probe against a live SCIM server.

    Side-effect consent is enforced by the caller (the web UI consent checkbox).
    """
    return run_probe_api(
        base_url=req.url,
        token=req.token,
        username=req.username,
        password=req.password,
        tls_no_verify=req.tls_no_verify,
        skip_cleanup=req.skip_cleanup,
        resource_filter=req.resource,
        strict=req.strict,
        timeout=req.timeout,
        profile=req.profile,
        extra_user_fields=req.extra_user_fields,
        user_domain=req.user_domain,
        proxy=req.proxy,
        ca_bundle=req.ca_bundle,
    )


_EXAMPLES_RESPONSE_EXAMPLE = {
    "examples": [
        {
            "id": "valid-user-minimal",
            "name": "Minimal valid User",
            "description": "Smallest valid User payload — only the required userName attribute.",
            "resource_type": "User",
            "valid": True,
            "payload": {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "userName": "john.doe@example.com",
            },
        },
        {
            "id": "invalid-user-missing-username",
            "name": "User missing userName",
            "description": "Fails validation: userName is required per RFC 7643 §4.1.1.",
            "resource_type": "User",
            "valid": False,
            "payload": {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "name": {"givenName": "John"},
            },
        },
    ]
}


@app.get(
    "/api/examples",
    responses={
        200: {
            "description": "Curated RFC example payload library with valid and invalid cases",
            "content": {"application/json": {"example": _EXAMPLES_RESPONSE_EXAMPLE}},
        }
    },
)
def examples():
    """Return the curated example payload library."""
    from .examples import get_public_examples
    return {"examples": get_public_examples()}


# Catch-all: serve index.html for any path not matched above so React Router
# can handle client-side routes (/validate, /probe, /examples).
# Must be defined last so it never shadows /api/* endpoints.
@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    index = _WEB_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"error": "Frontend not built. Run: cd web && npm run build"}
