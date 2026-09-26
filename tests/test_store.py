from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager

import pytest

from curren.store import ReadStore


def test_store_connections_are_closed_after_each_use(tmp_path) -> None:
    store = ReadStore(tmp_path / "curren.db")
    store.initialize()

    with store._connect() as connection:
        connection.execute("SELECT 1")

    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")


class _TracingStore(ReadStore):
    statements: list[str]

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with super()._connect() as connection:
            connection.set_trace_callback(self.statements.append)
            yield connection


def test_status_reads_use_the_status_index(tmp_path) -> None:
    store = _TracingStore(tmp_path / "curren.db")
    store.statements = []
    store.initialize()
    store.statements.clear()

    store.list_signals(status="active")
    store.list_signals(status="closed", symbol="BTCUSDT")
    store.public_summary()

    reads = [sql for sql in store.statements if sql.lstrip().upper().startswith("SELECT")]
    assert reads
    with closing(sqlite3.connect(tmp_path / "curren.db")) as connection:
        plans = [" | ".join(row[3] for row in connection.execute(f"EXPLAIN QUERY PLAN {sql}")) for sql in reads]
    assert not [plan for plan in plans if "SCAN signals" in plan], plans
