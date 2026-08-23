from __future__ import annotations

import os
from typing import Any

from curren.client import CurrenClient


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
            "Curren tools do not execute trades."
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
        """Get recent closed Curren signal results."""
        async with CurrenClient() as client:
            result = await client.get_recent_results(limit=limit)
        return result.model_dump(mode="json")

    @server.tool(name="curren_get_track_record")
    async def get_track_record() -> dict[str, Any]:
        """Get the server-published Curren track record and methodology label."""
        async with CurrenClient() as client:
            result = await client.get_track_record()
        return result.model_dump(mode="json")

    @server.tool(name="curren_verify_signal")
    async def verify_signal(signal_id: str) -> dict[str, Any]:
        """Verify the publication timestamp and content hash for a Curren signal."""
        async with CurrenClient() as client:
            result = await client.verify_signal(signal_id)
        return result.model_dump(mode="json")

    return server


mcp = _server()


def main() -> None:
    transport = os.getenv("CURREN_MCP_TRANSPORT", "stdio").strip().lower()
    if transport not in {"stdio", "streamable-http"}:
        raise SystemExit("CURREN_MCP_TRANSPORT must be 'stdio' or 'streamable-http'")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
