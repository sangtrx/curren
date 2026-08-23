from __future__ import annotations

import os
from typing import Any

from curren.client import CurrenClient

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def _server():
    try:
        from mcp.server import MCPServer
    except ImportError as exc:  # pragma: no cover - exercised by packaging, not runtime tests
        raise RuntimeError("MCP support is not installed. Install curren[mcp].") from exc

    server = MCPServer(
        "Curren",
        instructions=(
            "Use Curren as a read-only source of server-published crypto trading intelligence. "
            "Never infer restricted entry, stop, target, or lifecycle fields when the API omits them. "
            "Verification hashes check Curren's immutable initial publication and terminal outcome records; "
            "they are not independent timestamp or profitability proofs. Curren tools do not execute trades."
        ),
    )

    @server.tool(name="curren_list_active_signals")
    async def list_active_signals(symbol: str | None = None, limit: int = 20) -> dict[str, Any]:
        """List active Curren signals available to the current API entitlement."""
        async with CurrenClient() as client:
            result = await client.list_active_signals(symbol=symbol, limit=limit)
        return result.model_dump(mode="json")

    @server.tool(name="curren_get_signal")
    async def get_signal(signal_id: str) -> dict[str, Any]:
        """Get one Curren signal by immutable public signal id."""
        async with CurrenClient() as client:
            result = await client.get_signal(signal_id)
        return result.model_dump(mode="json")

    @server.tool(name="curren_get_signal_lifecycle")
    async def get_signal_lifecycle(signal_id: str) -> dict[str, Any]:
        """Get the published lifecycle events for one Curren signal."""
        async with CurrenClient() as client:
            items = await client.get_signal_lifecycle(signal_id)
        return {"items": [item.model_dump(mode="json") for item in items]}

    @server.tool(name="curren_get_recent_results")
    async def get_recent_results(limit: int = 20) -> dict[str, Any]:
        """Get recent proof-backed terminal Curren signal results."""
        async with CurrenClient() as client:
            result = await client.get_recent_results(limit=limit)
        return result.model_dump(mode="json")

    @server.tool(name="curren_get_track_record")
    async def get_track_record() -> dict[str, Any]:
        """Get the Curren track record derived from immutable outcome records."""
        async with CurrenClient() as client:
            result = await client.get_track_record()
        return result.model_dump(mode="json")

    @server.tool(name="curren_verify_signal")
    async def verify_signal(signal_id: str) -> dict[str, Any]:
        """Verify Curren's recorded plan and, when terminal, outcome integrity records."""
        async with CurrenClient() as client:
            result = await client.verify_signal(signal_id)
        return result.model_dump(mode="json")

    return server


mcp = _server()


def main() -> None:
    transport = os.getenv("CURREN_MCP_TRANSPORT", "stdio").strip().lower()
    if transport not in {"stdio", "streamable-http"}:
        raise SystemExit("CURREN_MCP_TRANSPORT must be 'stdio' or 'streamable-http'")
    if transport == "stdio":
        mcp.run(transport="stdio")
        return
    host = os.getenv("CURREN_MCP_HOST", "127.0.0.1").strip()
    _require_safe_http_host(host)
    port = int(os.getenv("CURREN_MCP_PORT", "8001"))
    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        stateless_http=True,
        json_response=True,
    )


def _require_safe_http_host(host: str) -> None:
    if host not in _LOOPBACK_HOSTS:
        raise SystemExit(
            "Curren MCP v0.4 refuses non-loopback Streamable HTTP binds because the bundled MCP server has no "
            "OAuth resource-server gate. Use stdio/localhost, or deploy a separately authenticated MCP gateway."
        )


if __name__ == "__main__":
    main()
