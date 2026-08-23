from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any

import typer

from curren.client import CurrenClient, CurrenError
from curren.models import Signal

app = typer.Typer(
    name="curren",
    help="Read-only Curren trading intelligence from the terminal.",
    no_args_is_help=True,
)


def _run(coro: Any) -> Any:
    try:
        return asyncio.run(coro)
    except (CurrenError, ValueError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


async def _active(symbol: str | None, limit: int):
    async with CurrenClient() as client:
        return await client.list_active_signals(symbol=symbol, limit=limit)


@app.command("signals")
def signals(
    symbol: str | None = typer.Option(None, "--symbol", "-s", help="Filter by symbol, e.g. HYPEUSDT."),
    limit: int = typer.Option(20, min=1, max=100),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
) -> None:
    """List active signals available to the current API entitlement."""
    result = _run(_active(symbol, limit))
    if json_output:
        _echo_json(result.model_dump(mode="json"))
        return
    if not result.items:
        typer.echo("No active signals available.")
        return
    _print_signals(result.items)


async def _signal(signal_id: str):
    async with CurrenClient() as client:
        return await client.get_signal(signal_id)


@app.command("signal")
def signal(
    signal_id: str,
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Get one signal by immutable public signal id."""
    item = _run(_signal(signal_id))
    if json_output:
        _echo_json(item.model_dump(mode="json"))
        return
    _print_signal_detail(item)


async def _results(limit: int):
    async with CurrenClient() as client:
        return await client.get_recent_results(limit=limit)


@app.command("results")
def results(
    limit: int = typer.Option(20, min=1, max=100),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show recent closed signal results."""
    result = _run(_results(limit))
    if json_output:
        _echo_json(result.model_dump(mode="json"))
        return
    if not result.items:
        typer.echo("No results available.")
        return
    _print_signals(result.items)


async def _track_record():
    async with CurrenClient() as client:
        return await client.get_track_record()


@app.command("track-record")
def track_record(json_output: bool = typer.Option(False, "--json")) -> None:
    """Show the server-published Curren track record."""
    record = _run(_track_record())
    if json_output:
        _echo_json(record.model_dump(mode="json"))
        return
    typer.echo(f"Sample size : {record.sample_size}")
    typer.echo(f"Wins        : {_value(record.wins)}")
    typer.echo(f"Losses      : {_value(record.losses)}")
    typer.echo(f"Win rate    : {_pct(record.win_rate)}")
    typer.echo(f"Net R       : {_number(record.net_r)}")
    typer.echo(f"Average R   : {_number(record.average_r)}")
    typer.echo(f"As of       : {_time(record.as_of)}")
    if record.methodology:
        typer.echo(f"Methodology : {record.methodology}")


async def _verify(signal_id: str):
    async with CurrenClient() as client:
        return await client.verify_signal(signal_id)


@app.command("verify")
def verify(
    signal_id: str,
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Verify the server-published immutable publication record for a signal."""
    record = _run(_verify(signal_id))
    if json_output:
        _echo_json(record.model_dump(mode="json"))
        return
    state = "VERIFIED" if record.verified else "NOT VERIFIED"
    typer.echo(f"{state} {record.signal_id}")
    typer.echo(f"Published : {_time(record.published_at)}")
    typer.echo(f"Hash      : {record.content_hash}")
    if record.record_version:
        typer.echo(f"Version   : {record.record_version}")


def _print_signals(items: list[Signal]) -> None:
    typer.echo(f"{'SYMBOL':<14} {'SIDE':<6} {'STATUS':<12} {'R':>8} {'PUBLISHED':>20}")
    for item in items:
        typer.echo(
            f"{item.symbol:<14} {str(item.side).upper():<6} {str(item.status):<12} "
            f"{_number(item.realized_r if item.realized_r is not None else item.current_r):>8} "
            f"{_time(item.published_at):>20}"
        )


def _print_signal_detail(item: Signal) -> None:
    typer.echo(f"{item.symbol} {str(item.side).upper()} · {item.status}")
    typer.echo(f"Signal ID : {item.id}")
    typer.echo(f"Published : {_time(item.published_at)}")
    typer.echo(f"Entry     : {_number(item.entry)}")
    typer.echo(f"Mark      : {_number(item.mark)}")
    typer.echo(f"Stop      : {_number(item.stop)}")
    typer.echo(f"Current R : {_number(item.current_r)}")
    typer.echo(f"Peak R    : {_number(item.peak_r)}")
    typer.echo(f"Realized R: {_number(item.realized_r)}")
    if item.targets:
        for index, target in enumerate(item.targets, start=1):
            typer.echo(f"TP{index:<8}: {_number(target.price)} · {target.status}")
    if item.entry is None or item.stop is None:
        typer.echo("Exact trade levels are not available to this entitlement.")


def _echo_json(value: Any) -> None:
    typer.echo(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def _value(value: object | None) -> str:
    return "—" if value is None else str(value)


def _number(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}"


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value:.1%}"


def _time(value: datetime | None) -> str:
    return "—" if value is None else value.isoformat(timespec="seconds")


if __name__ == "__main__":
    app()
