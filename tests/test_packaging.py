from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import curren

REPO_ROOT = Path(__file__).resolve().parents[1]


def _pyproject() -> dict:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_license_expression_is_not_mixed_with_legacy_license_classifiers() -> None:
    # setuptools rejects PEP 639 `license = "<SPDX>"` combined with `License ::`
    # classifiers, which breaks `pip install`, `python -m build`, and `docker build`.
    project = _pyproject()["project"]
    assert isinstance(project["license"], str)
    assert not [item for item in project.get("classifiers", []) if item.startswith("License ::")]


def test_release_version_is_consistent_across_distribution_surfaces() -> None:
    version = _pyproject()["project"]["version"]
    manifest = json.loads((REPO_ROOT / "manifest.json").read_text(encoding="utf-8"))
    sources = "\n".join(
        (REPO_ROOT / "src" / "curren" / name).read_text(encoding="utf-8")
        for name in ("client.py", "publisher.py", "server.py")
    )

    assert curren.__version__ == version
    assert manifest["version"] == version
    assert f"curren-python/{version}" in sources
    assert f"curren-publisher/{version}" in sources
    assert f'version="{version}"' in sources


def test_importing_server_has_no_database_or_env_side_effects(tmp_path) -> None:
    environment = {**os.environ, "CURREN_API_KEYS_JSON": "not-json"}
    environment.pop("CURREN_DB_PATH", None)
    completed = subprocess.run(
        [sys.executable, "-c", "import curren.server"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert not (tmp_path / ".local").exists()


def test_server_module_still_exposes_asgi_app_on_demand(tmp_path, monkeypatch) -> None:
    import curren.server

    monkeypatch.setenv("CURREN_DB_PATH", str(tmp_path / "curren.db"))
    assert curren.server.app.title == "Curren API"
    assert (tmp_path / "curren.db").exists()
