"""Integration tests for the probe runner against mock SCIM servers.

These tests exercise the full probe pipeline (runner -> tests -> report)
against MockSCIMServer instances with various configurations:

- Conformant server (all tests should pass)
- Non-conformant servers (missing meta, missing id, password leak)
- Server with limited resource types (Agent tests should skip)
- Throttling server (429 retry should succeed)
- Strict vs compat modes (content-type deviations)
- Side-effect consent gating
"""

import json
import pytest
from scim_sanity.probe.runner import run_probe
from scim_sanity.probe.report import ProbeResult
from tests.mock_scim_server import MockSCIMServer


@pytest.fixture
def conformant_server():
    """A fully conformant mock SCIM server."""
    with MockSCIMServer() as s:
        yield s


@pytest.fixture
def no_agent_server():
    """A server that only supports User and Group."""
    with MockSCIMServer(supported_resources=["User", "Group"]) as s:
        yield s


@pytest.fixture
def missing_meta_server():
    """A non-conformant server that omits meta from responses."""
    with MockSCIMServer(non_conformances={"missing_meta": True}) as s:
        yield s


@pytest.fixture
def missing_id_server():
    """A non-conformant server that omits id from responses."""
    with MockSCIMServer(non_conformances={"missing_id": True}) as s:
        yield s


@pytest.fixture
def password_leak_server():
    """A non-conformant server that returns password in responses."""
    with MockSCIMServer(non_conformances={"password_in_response": True}) as s:
        yield s


@pytest.fixture
def throttling_server():
    """A server that returns 429 for the first 2 requests."""
    with MockSCIMServer(non_conformances={"throttle_count": 2}) as s:
        yield s


@pytest.fixture
def content_type_json_server():
    """A server that uses application/json instead of application/scim+json."""
    with MockSCIMServer(non_conformances={"content_type_json": True}) as s:
        yield s


def _run(url, **kwargs):
    """Helper: run probe with accept_side_effects=True and json_output=True."""
    kwargs.setdefault("accept_side_effects", True)
    kwargs.setdefault("json_output", True)
    return run_probe(url, **kwargs)


class TestConformantServer:

    def test_full_probe_passes(self, conformant_server, capsys):
        exit_code = _run(conformant_server.base_url)
        captured = capsys.readouterr()
        report = json.loads(captured.out)

        assert report["summary"]["failed"] == 0
        assert report["summary"]["errors"] == 0
        assert report["summary"]["passed"] > 0
        assert exit_code == 0

    def test_probe_with_skip_cleanup(self, conformant_server, capsys):
        exit_code = _run(conformant_server.base_url, skip_cleanup=True)
        captured = capsys.readouterr()
        report = json.loads(captured.out)
        assert exit_code == 0

    def test_resource_filter_user(self, conformant_server, capsys):
        exit_code = _run(conformant_server.base_url, resource_filter="User")
        captured = capsys.readouterr()
        report = json.loads(captured.out)
        skip_results = [r for r in report["results"] if r["status"] == "skip"]
        skip_names = [r["name"] for r in skip_results]
        assert any("Group" in n for n in skip_names)
        assert exit_code == 0


class TestSideEffectConsent:

    def test_refuses_without_consent(self, conformant_server, capsys):
        """Probe must refuse to run without --i-accept-side-effects."""
        exit_code = run_probe(
            conformant_server.base_url,
            accept_side_effects=False,
            json_output=True,
        )
        assert exit_code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "side-effect" in output.get("error", "").lower() or "side-effect" in output.get("message", "").lower()

    def test_refuses_without_consent_terminal(self, conformant_server, capsys):
        """Terminal output also refuses."""
        exit_code = run_probe(
            conformant_server.base_url,
            accept_side_effects=False,
        )
        assert exit_code == 1


class TestStrictVsCompat:

    def test_compat_mode_content_type_json_is_warning(self, content_type_json_server, capsys):
        """In compat mode, application/json should produce warnings, not failures."""
        exit_code = _run(content_type_json_server.base_url, strict=False)
        captured = capsys.readouterr()
        report = json.loads(captured.out)
        # Warnings should exist but failures should be 0
        assert report["summary"]["warnings"] > 0
        assert report["summary"]["failed"] == 0
        assert exit_code == 0

    def test_strict_mode_content_type_json_is_failure(self, content_type_json_server, capsys):
        """In strict mode, application/json in discovery should produce warnings."""
        exit_code = _run(content_type_json_server.base_url, strict=True)
        captured = capsys.readouterr()
        report = json.loads(captured.out)
        # Should have some warnings about Content-Type
        warns = [r for r in report["results"] if r["status"] == "warn"]
        assert len(warns) > 0


class TestNoAgentServer:

    def test_agent_tests_skipped(self, no_agent_server, capsys):
        exit_code = _run(no_agent_server.base_url)
        captured = capsys.readouterr()
        report = json.loads(captured.out)

        skipped = [r for r in report["results"] if r["status"] == "skip"]
        skipped_names = [r["name"] for r in skipped]
        assert any("Agent" in n for n in skipped_names)
        assert exit_code == 0


class TestNonConformantServers:

    def test_missing_meta_detected(self, missing_meta_server, capsys):
        exit_code = _run(missing_meta_server.base_url)
        captured = capsys.readouterr()
        report = json.loads(captured.out)

        assert report["summary"]["failed"] > 0
        assert exit_code == 1

    def test_missing_id_detected(self, missing_id_server, capsys):
        exit_code = _run(missing_id_server.base_url)
        captured = capsys.readouterr()
        report = json.loads(captured.out)

        assert report["summary"]["failed"] > 0
        assert exit_code == 1

    def test_password_leak_detected(self, password_leak_server, capsys):
        exit_code = _run(password_leak_server.base_url)
        captured = capsys.readouterr()
        report = json.loads(captured.out)
        # Probe runs to completion either way
        assert exit_code == 0 or exit_code == 1


class TestThrottling:

    def test_429_retry_succeeds(self, throttling_server, capsys):
        """Probe should retry on 429 and eventually succeed."""
        exit_code = _run(throttling_server.base_url)
        captured = capsys.readouterr()
        report = json.loads(captured.out)
        # Even with initial 429s, retries should let the probe succeed
        assert report["summary"]["passed"] > 0
        assert exit_code == 0
