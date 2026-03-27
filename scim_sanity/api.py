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


@app.post("/api/validate")
def validate(req: ValidateRequest):
    """Validate a SCIM payload against RFC 7643/7644 rules."""
    validator = SCIMValidator()
    is_valid, errors = validator.validate(req.payload, req.operation)
    return {
        "valid": is_valid,
        "errors": [e.to_dict() for e in errors],
    }


@app.post("/api/probe")
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
    )


@app.get("/api/examples")
def examples():
    """Return the curated example payload library."""
    from .examples import get_public_examples
    return {"examples": get_public_examples()}


# Catch-all: serve index.html for any path not matched above so React Router
# can handle client-side routes (/validate, /probe, /examples).
# Must be defined last so it never shadows /api/* endpoints.
@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    index = _WEB_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"error": "Frontend not built. Run: cd web && npm run build"}
