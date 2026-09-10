"""Release guard and workflow contract tests."""

import importlib
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

check_index_version = importlib.import_module("check_index_version")
check_release_tag = importlib.import_module("check_release_tag")


def test_project_uses_apache_2_license():
    project = check_release_tag.tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    notice_text = (ROOT / "NOTICE").read_text(encoding="utf-8")

    assert project["license"] == "Apache-2.0"
    assert "License :: OSI Approved :: Apache Software License" in project["classifiers"]
    assert "Apache License" in license_text
    assert "Version 2.0, January 2004" in license_text
    assert "GNU GENERAL PUBLIC LICENSE" not in license_text
    assert "GNU General Public License" not in notice_text


def test_release_tag_must_match_declared_version():
    assert check_release_tag.validate_tag("v0.1.0") == "v0.1.0"
    with pytest.raises(ValueError, match="release tag must be"):
        check_release_tag.validate_tag("v0.1.1")


def test_release_tag_rejects_inconsistent_package_version(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "fastapi-nacos-extension"\nversion = "9.9.9"\n',
        encoding="utf-8",
    )
    package = tmp_path / "fastapi_nacos_extension"
    package.mkdir()
    (package / "__init__.py").write_text('__version__ = "0.1.0"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="version mismatch"):
        check_release_tag.declared_version(tmp_path)


def test_index_preflight_accepts_missing_version(monkeypatch):
    def missing(*_args, **_kwargs):
        raise HTTPError("https://example.invalid", 404, "not found", None, None)

    monkeypatch.setattr(check_index_version, "urlopen", missing)
    assert check_index_version.ensure_version_available("pypi") == (
        "fastapi-nacos-extension",
        "0.1.0",
    )


def test_index_preflight_rejects_existing_version(monkeypatch):
    class Response:
        def close(self):
            return None

    monkeypatch.setattr(check_index_version, "urlopen", lambda *_args, **_kwargs: Response())
    with pytest.raises(ValueError, match="already exists on testpypi"):
        check_index_version.ensure_version_available("testpypi")


def test_index_preflight_fails_closed_on_network_error(monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise URLError("offline")

    monkeypatch.setattr(check_index_version, "urlopen", unavailable)
    with pytest.raises(RuntimeError, match="index preflight failed"):
        check_index_version.ensure_version_available("pypi")


def test_release_workflow_uses_verified_artifact_and_trusted_publishing():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch" in workflow
    assert "python scripts/check_release_tag.py" in workflow
    assert "python scripts/check_index_version.py testpypi" in workflow
    assert "python scripts/check_index_version.py pypi" in workflow
    assert "uses: actions/upload-artifact@v4" in workflow
    assert workflow.count("uses: actions/download-artifact@v4") == 2
    assert workflow.count("uses: pypa/gh-action-pypi-publish@release/v1") == 2
    assert "name: testpypi" in workflow
    assert "name: pypi" in workflow
    assert "id-token: write" in workflow
    assert "softprops/action-gh-release" not in workflow
    assert "contents: write" not in workflow
