from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_repo_root_is_an_omarchy_plugin() -> None:
    manifest = json.loads((REPO_ROOT / "manifest.json").read_text())

    assert manifest["schemaVersion"] == 1
    assert manifest["id"] == "tech.curren.signals"
    assert "bar-widget" in manifest["kinds"]
    entry_point = REPO_ROOT / manifest["entryPoints"]["barWidget"]
    assert entry_point.is_file()


def test_omarchy_plugin_does_not_embed_private_credentials() -> None:
    qml = "\n".join(path.read_text() for path in (REPO_ROOT / "omarchy").glob("*.qml"))
    lowered = qml.lower()

    assert "curren_api_key" not in lowered
    assert "authorization" not in lowered
    assert "trade_intent" not in lowered
    assert "place_order" not in lowered
