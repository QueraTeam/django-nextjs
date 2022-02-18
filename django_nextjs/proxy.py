import asyncio
import re

import aiohttp
import requests
import websockets
from channels.generic.http import AsyncHttpConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from django import http
from django.conf import settings
from django.views import View

from django_nextjs.app_settings import NEXTJS_SERVER_URL
from django_nextjs.exceptions import NextJSImproperlyConfigured


class NextJSProxyHttpConsumer(AsyncHttpConsumer):
    """
    Proxies /next..., /_next..., /__nextjs... requests to Next.js server in development environment.

    - This is an async consumer for django channels.
    - Supports streaming response.
    """

    async def handle(self, body):
        if not settings.DEBUG:
            raise NextJSImproperlyConfigured("This proxy is for development only.")
        url = NEXTJS_SERVER_URL + self.scope["path"] + "?" + self.scope["query_string"].decode()
        headers = {k.decode(): v.decode() for k, v in self.scope["headers"]}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                await self.send_headers(
                    headers=[
                        (b"Content-Type", response.headers["content-type"].encode()),
                    ]
                )
                async for data in response.content.iter_any():
                    await self.send_body(data, more_body=True)
                await self.send_body(b"", more_body=False)


class NextJSProxyWebsocketConsumer(AsyncWebsocketConsumer):
    """
    Proxies websocket requests to Next.js server in development environment.

    - This is an async consumer for django channels.
    - Use this for nextjs 12 and above to activate webpack hmr.
    """

    async def connect_to_nextjs_server(self):
        url = "ws://" + re.match(r".+://(.+:\d+)", NEXTJS_SERVER_URL).group(1) + self.scope["path"]
        self.websocket_nextjs = await websockets.connect(url)

    async def connect(self):
        await self.connect_to_nextjs_server()
        await self.accept()

        async def receive_from_nextjs_server():
            async for message in self.websocket_nextjs:
                await self.send(message)

        asyncio.ensure_future(receive_from_nextjs_server())

    async def receive(self, text_data=None, bytes_data=None):
        """received message from browser"""
        try:
            await self.websocket_nextjs.send(text_data)
        except websockets.ConnectionClosed:
            await self.connect_to_nextjs_server()

    async def close(self, code=None):
        await self.websocket_nextjs.close()


class NextJSProxyView(View):
    """
    Proxies /next..., /_next..., /__nextjs... requests to Next.js server in development environment.
    Source: https://github.com/yourlabs/djnext/blob/master/src/djnext/views.py

    - This is a normal django view.
    - Supports streaming response.
    """

    def dispatch(self, request, *args, **kwargs):
        if not settings.DEBUG:
            raise NextJSImproperlyConfigured("This proxy is for development only.")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        url = NEXTJS_SERVER_URL + request.path + "?" + request.GET.urlencode()

        if request.headers.get("Accept", None) == "text/event-stream":
            response = requests.get(url, stream=True, cookies=request.COOKIES)
            ret = http.StreamingHttpResponse(response.iter_content())
        else:
            response = requests.get(url, cookies=request.COOKIES)
            ret = http.HttpResponse(
                content=bytes(response.content),
            )

        if "Content-Type" in response.headers:
            ret["Content-Type"] = response.headers["Content-Type"]
        return ret
