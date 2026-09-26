from __future__ import annotations

import json
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

