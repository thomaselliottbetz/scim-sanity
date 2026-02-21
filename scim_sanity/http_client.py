"""Thin HTTP abstraction for talking to SCIM servers.

Uses ``requests`` if installed, otherwise falls back to ``urllib.request``
from stdlib.  This mirrors the Click fallback pattern used in cli.py —
zero runtime dependencies, but better ergonomics when optional packages
are available.

Key behaviors:
- Automatic 429 Too Many Requests retry with Retry-After header support
- Bearer token and HTTP Basic authentication
- TLS options: skip verification, custom CA bundle
- Proxy support via urllib or requests
- ``redact_auth()`` helper for safe logging of headers
"""

import json
import ssl
import time
from typing import Any, Dict, Optional, Tuple

# Optional dependency: use requests if available, fall back to urllib
try:
    import requests as _requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

import urllib.request
import urllib.error


# Retry policy for 429 Too Many Requests (RFC 6585)
_MAX_RETRIES = 3
_DEFAULT_RETRY_AFTER = 2  # seconds, used when Retry-After header is missing


class SCIMResponse:
    """Normalized HTTP response wrapper.

    Provides a consistent interface regardless of whether the underlying
    request was made via ``requests`` or ``urllib``.
    """

    def __init__(self, status_code: int, headers: Dict[str, str], body: str):
        self.status_code = status_code
        self.headers = headers
        self.body = body
        self._json = None

    def json(self) -> Any:
        """Parse and cache the response body as JSON."""
        if self._json is None:
            self._json = json.loads(self.body) if self.body else None
        return self._json

    def header(self, name: str) -> Optional[str]:
        """Case-insensitive header lookup."""
        lower = name.lower()
        for k, v in self.headers.items():
            if k.lower() == lower:
                return v
        return None


class SCIMClient:
    """HTTP client for SCIM server interactions.

    Supports bearer token and basic auth, TLS configuration, proxy routing,
    and automatic retry on 429 responses.

    Args:
        base_url:       Root URL of the SCIM endpoint (e.g. ``https://example.com/scim/v2``)
        token:          Bearer token for authentication
        username:       Username for HTTP Basic authentication
        password:       Password for HTTP Basic authentication
        tls_no_verify:  Skip TLS certificate verification (for self-signed certs)
        timeout:        Per-request timeout in seconds
        proxy:          HTTP/HTTPS proxy URL
        ca_bundle:      Path to custom CA certificate bundle file
    """

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        tls_no_verify: bool = False,
        timeout: int = 30,
        proxy: Optional[str] = None,
        ca_bundle: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.username = username
        self.password = password
        self.tls_no_verify = tls_no_verify
        self.timeout = timeout
        self.proxy = proxy
        self.ca_bundle = ca_bundle

    # -- Public API ----------------------------------------------------------

    def get(self, path: str) -> SCIMResponse:
        """Send a GET request to the SCIM endpoint."""
        return self._request("GET", path)

    def post(self, path: str, payload: Dict[str, Any],
             extra_headers: Optional[Dict[str, str]] = None) -> SCIMResponse:
        """Send a POST request with a JSON payload."""
        return self._request("POST", path, payload, extra_headers=extra_headers)

    def put(self, path: str, payload: Dict[str, Any],
            extra_headers: Optional[Dict[str, str]] = None) -> SCIMResponse:
        """Send a PUT request with a JSON payload."""
        return self._request("PUT", path, payload, extra_headers=extra_headers)

    def patch(self, path: str, payload: Dict[str, Any],
              extra_headers: Optional[Dict[str, str]] = None) -> SCIMResponse:
        """Send a PATCH request with a JSON payload."""
        return self._request("PATCH", path, payload, extra_headers=extra_headers)

    def delete(self, path: str,
               extra_headers: Optional[Dict[str, str]] = None) -> SCIMResponse:
        """Send a DELETE request."""
        return self._request("DELETE", path, extra_headers=extra_headers)

    # -- Internals -----------------------------------------------------------

    def _build_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build the default SCIM request headers with auth credentials."""
        headers = {
            "Accept": "application/scim+json",
            "Content-Type": "application/scim+json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        elif self.username and self.password:
            import base64
            creds = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            headers["Authorization"] = f"Basic {creds}"
        if extra:
            headers.update(extra)
        return headers

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> SCIMResponse:
        """Execute an HTTP request with automatic 429 retry.

        Retries up to ``_MAX_RETRIES`` times when the server responds with
        429 Too Many Requests, sleeping for the duration specified by the
        ``Retry-After`` header (or ``_DEFAULT_RETRY_AFTER`` if absent).
        """
        url = f"{self.base_url}{path}"
        headers = self._build_headers(extra_headers)

        for attempt in range(_MAX_RETRIES + 1):
            if HAS_REQUESTS:
                resp = self._request_with_requests(method, url, headers, payload)
            else:
                resp = self._request_with_urllib(method, url, headers, payload)

            if resp.status_code == 429 and attempt < _MAX_RETRIES:
                retry_after = _parse_retry_after(resp.header("Retry-After"))
                time.sleep(retry_after)
                continue

            return resp

        return resp  # Return last response if all retries exhausted

    def _request_with_requests(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        payload: Optional[Dict[str, Any]],
    ) -> SCIMResponse:
        """Execute request using the ``requests`` library."""
        kwargs: Dict[str, Any] = {
            "headers": headers,
            "timeout": self.timeout,
        }
        if self.ca_bundle:
            kwargs["verify"] = self.ca_bundle
        elif self.tls_no_verify:
            kwargs["verify"] = False
        else:
            kwargs["verify"] = True

        if self.proxy:
            kwargs["proxies"] = {"http": self.proxy, "https": self.proxy}

        if payload is not None:
            kwargs["json"] = payload

        resp = _requests.request(method, url, **kwargs)
        resp_headers = dict(resp.headers)
        return SCIMResponse(resp.status_code, resp_headers, resp.text)

    def _request_with_urllib(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        payload: Optional[Dict[str, Any]],
    ) -> SCIMResponse:
        """Execute request using ``urllib.request`` from stdlib."""
        body_bytes = None
        if payload is not None:
            body_bytes = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)

        # Build SSL context for TLS configuration
        ctx = None
        if self.tls_no_verify:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        elif self.ca_bundle:
            ctx = ssl.create_default_context(cafile=self.ca_bundle)

        # Build opener with proxy handler if configured
        opener = None
        if self.proxy:
            proxy_handler = urllib.request.ProxyHandler({
                "http": self.proxy,
                "https": self.proxy,
            })
            opener = urllib.request.build_opener(proxy_handler)

        try:
            if opener:
                resp = opener.open(req, timeout=self.timeout)
            else:
                resp = urllib.request.urlopen(req, context=ctx, timeout=self.timeout)
            with resp:
                resp_body = resp.read().decode("utf-8", errors="replace")
                resp_headers = {k: v for k, v in resp.getheaders()}
                return SCIMResponse(resp.status, resp_headers, resp_body)
        except urllib.error.HTTPError as e:
            # urllib raises HTTPError for non-2xx responses; normalize to SCIMResponse
            resp_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            resp_headers = {k: v for k, v in e.headers.items()} if e.headers else {}
            return SCIMResponse(e.code, resp_headers, resp_body)


def _parse_retry_after(value: Optional[str]) -> float:
    """Parse a Retry-After header value into seconds to wait.

    Handles integer-second values per RFC 7231 Section 7.1.3.
    Returns ``_DEFAULT_RETRY_AFTER`` if the header is missing or unparseable.
    Always returns at least 1.0 second to avoid busy-loop retries.
    """
    if not value:
        return _DEFAULT_RETRY_AFTER
    try:
        return max(1.0, float(value))
    except ValueError:
        return _DEFAULT_RETRY_AFTER


def redact_auth(headers: Dict[str, str]) -> Dict[str, str]:
    """Return a copy of headers with Authorization values replaced by ``***REDACTED***``.

    Use this when including headers in JSON output, logs, or error messages
    to avoid leaking bearer tokens or basic auth credentials.
    """
    redacted = dict(headers)
    for key in list(redacted.keys()):
        if key.lower() == "authorization":
            redacted[key] = "***REDACTED***"
    return redacted
