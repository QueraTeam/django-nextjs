import asyncio
from unittest.mock import AsyncMock, patch
from urllib.parse import urlparse

import pytest

from django_nextjs.app_settings import NEXTJS_SERVER_URL
from django_nextjs.asgi import NextJsWebSocketProxy


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query_scope,expected_suffix",
    [
        ({}, ""),
        ({"query_string": None}, ""),
        ({"query_string": b""}, ""),
        (
            {"query_string": b"id=document%2B123&value=a%26b%3Dc&value=c+d&value=e%20f"},
            "?id=document%2B123&value=a%26b%3Dc&value=c+d&value=e%20f",
        ),
    ],
)
async def test_websocket_proxy_preserves_query_string(settings, query_scope, expected_suffix):
    settings.DEBUG = True
    proxy = NextJsWebSocketProxy()
    proxy.scope = {"path": "/_next/webpack-hmr", **query_scope}
    proxy.send = AsyncMock()
    connection = AsyncMock()

    with (
        patch("django_nextjs.asgi.websockets.connect", AsyncMock(return_value=connection)) as connect,
        patch.object(proxy, "_receive_from_nextjs_server", AsyncMock()),
    ):
        try:
            await proxy.connect()
            expected_url = f"ws://{urlparse(NEXTJS_SERVER_URL).netloc}/_next/webpack-hmr{expected_suffix}"
            connect.assert_awaited_once_with(expected_url)
            proxy.send.assert_awaited_once_with({"type": "websocket.accept"})
        finally:
            listener = proxy.nextjs_listener_task
            await proxy.disconnect()
            if listener is not None:
                await asyncio.gather(listener, return_exceptions=True)
