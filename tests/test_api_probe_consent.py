import pytest

pytest.importorskip("fastapi")

from fastapi import HTTPException

from scim_sanity.api import ProbeRequest, probe


def test_probe_endpoint_requires_side_effect_consent():
    """The REST API must refuse to run the destructive probe without consent."""
    with pytest.raises(HTTPException) as exc:
        probe(ProbeRequest(url="http://127.0.0.1:9/scim/v2"))
    assert exc.value.status_code == 400
    assert "i_accept_side_effects" in exc.value.detail


def test_probe_endpoint_runs_with_consent():
    from tests.mock_scim_server import MockSCIMServer

    with MockSCIMServer() as s:
        result = probe(ProbeRequest(url=s.base_url, timeout=5, i_accept_side_effects=True))
    assert "summary" in result
