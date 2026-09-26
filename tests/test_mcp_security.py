from __future__ import annotations

import pytest

from curren.mcp_server import _require_safe_http_host, mcp


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
def test_mcp_streamable_http_allows_loopback(host: str) -> None:
    _require_safe_http_host(host)


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.0.2.10"])
def test_mcp_streamable_http_rejects_public_bind_without_auth(host: str) -> None:
    with pytest.raises(SystemExit, match="refuses non-loopback"):
        _require_safe_http_host(host)


async def test_mcp_exposes_only_the_six_read_only_tools() -> None:
    tools = await mcp.list_tools()

    assert sorted(tool.name for tool in tools) == [
        "curren_get_recent_results",
        "curren_get_signal",
        "curren_get_signal_lifecycle",
        "curren_get_track_record",
        "curren_list_active_signals",
        "curren_verify_signal",
    ]
    assert all(tool.annotations is not None and tool.annotations.read_only_hint is True for tool in tools)
