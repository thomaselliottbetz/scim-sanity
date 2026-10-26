"""Guards against shipping a wheel without the web GUI (missing from 0.6.0-0.7.3)."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def test_pyproject_ships_built_frontend():
    text = (ROOT / "pyproject.toml").read_text()
    assert "[tool.setuptools.package-data]" in text
    assert '"static/*"' in text and '"static/assets/*"' in text


def test_api_serves_frontend_from_inside_package():
    pytest.importorskip("fastapi")
    from scim_sanity import api

    assert api._WEB_DIST == ROOT / "scim_sanity" / "static"


def test_missing_frontend_returns_503(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from scim_sanity import api

    monkeypatch.setattr(api, "_WEB_DIST", tmp_path)
    resp = api.serve_frontend("validate")
    assert resp.status_code == 503
