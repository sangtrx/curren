"""Static drift checks between the Supabase bridge and the canonical publication contract.

These run in the default gate without Docker; tests/test_supabase_bridge_parity.py exercises the
bridge end to end.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from annotated_types import MaxLen

from curren import models
from curren.models import (
    PublicationBatch,
    PublicationLifecycleEvent,
    PublicationSignal,
    PublicationTarget,
    SignalSide,
    SignalStatus,
    TargetStatus,
)

REPO = Path(__file__).resolve().parents[1]
BRIDGE = (REPO / "supabase" / "functions" / "curren-api" / "index.ts").read_text()
MIGRATION = (REPO / "supabase" / "migrations" / "20260927090000_publication_ingest_parity.sql").read_text()
STORE = (REPO / "src" / "curren" / "store.py").read_text()


def _ts_set(name: str) -> set[str]:
    match = re.search(rf"const {name} = new Set\(\[(.*?)\]\);", BRIDGE, re.DOTALL)
    assert match, name
    return set(re.findall(r'"([^"]+)"', match.group(1)))


def _ts_number(name: str) -> int:
    match = re.search(rf"const {name} = (\d+);", BRIDGE)
    assert match, name
    return int(match.group(1))


def _ts_regex(name: str) -> str:
    match = re.search(rf"const {name} = /(.*?)/;", BRIDGE)
    assert match, name
    return match.group(1)


def _max_length(model, field: str) -> int:
    return next(item.max_length for item in model.model_fields[field].metadata if isinstance(item, MaxLen))


@pytest.mark.parametrize(
    ("constant", "model"),
    [
        ("BATCH_KEYS", PublicationBatch),
        ("SIGNAL_KEYS", PublicationSignal),
        ("TARGET_KEYS", PublicationTarget),
        ("LIFECYCLE_KEYS", PublicationLifecycleEvent),
    ],
)
def test_bridge_accepts_exactly_the_publication_fields(constant: str, model) -> None:
    assert _ts_set(constant) == set(model.model_fields)


def test_bridge_enums_and_limits_match_the_models() -> None:
    assert _ts_set("SIGNAL_STATUSES") == {status.value for status in SignalStatus}
    assert _ts_set("TERMINAL_STATUSES") == {status.value for status in models.TERMINAL_SIGNAL_STATUSES}
    assert _ts_set("SIGNAL_SIDES") == {side.value for side in SignalSide}
    assert _ts_set("TARGET_STATUSES") == {status.value for status in TargetStatus}
    assert _ts_number("MAX_SIGNALS") == _max_length(PublicationBatch, "signals")
    assert _ts_number("MAX_TARGETS") == _max_length(PublicationSignal, "targets")
    assert _ts_number("MAX_LIFECYCLE_EVENTS") == _max_length(PublicationSignal, "lifecycle")
    assert _ts_regex("SIGNAL_ID") == models._SIGNAL_ID_RE.pattern
    assert _ts_regex("SYMBOL") == models._SYMBOL_RE.pattern
    assert _ts_regex("PUBLIC_NAME") == models._NAME_RE.pattern


@pytest.mark.parametrize(
    "message",
    [
        "publication source changed for",
        "terminal signal cannot return to a live state for",
        "immutable publication fields changed for",
        "immutable terminal outcome changed for",
        "immutable terminal projection changed for",
        "immutable lifecycle event changed for",
    ],
)
def test_bridge_conflicts_use_the_reference_messages(message: str) -> None:
    assert message in STORE
    assert f"'{message} %'" in MIGRATION
