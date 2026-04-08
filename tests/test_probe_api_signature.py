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

