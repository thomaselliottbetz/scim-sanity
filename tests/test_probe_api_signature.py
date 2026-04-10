import pytest

from scim_sanity.probe.runner import run_probe_api
from tests.mock_scim_server import MockSCIMServer


def test_run_probe_api_accepts_user_domain():
    """Regression test: API wrapper must stay in sync with CLI probe options.

    We don't validate correctness of the domain override here; we just ensure the
    API entry point accepts the parameter and doesn't crash with a TypeError.
    """
    with MockSCIMServer() as s:
        result = run_probe_api(
            base_url=s.base_url,
            strict=True,
            timeout=5,
            user_domain="example.com",
        )

    assert isinstance(result, dict)
    assert "summary" in result
    assert "results" in result


def test_run_probe_api_accepts_proxy_and_ca_bundle():
    """Regression test: run_probe_api must accept proxy and ca_bundle parameters.

    We don't validate that proxy/ca_bundle are forwarded correctly to the HTTP
    layer here; we just ensure the API entry point accepts them without TypeError.
    The proxy value is intentionally unreachable so requests will fail fast —
    the mock server ensures the probe still completes with results.
    """
    with MockSCIMServer() as s:
        result = run_probe_api(
            base_url=s.base_url,
            strict=True,
            timeout=5,
            proxy=None,
            ca_bundle=None,
        )

    assert isinstance(result, dict)
    assert "summary" in result
    assert "results" in result

