from __future__ import annotations

import pytest

from curren.mcp_server import _require_safe_http_host


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
def test_mcp_streamable_http_allows_loopback(host: str) -> None:
    _require_safe_http_host(host)


@pytest.mark.parametrize("host", ["0.0.0.0", "::", "192.0.2.10"])
def test_mcp_streamable_http_rejects_public_bind_without_auth(host: str) -> None:
    with pytest.raises(SystemExit, match="refuses non-loopback"):
        _require_safe_http_host(host)
