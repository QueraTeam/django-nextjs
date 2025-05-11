import asyncio
import urllib.request
from http.client import HTTPResponse
from typing import Optional
from urllib.parse import urlparse

import aiohttp
import websockets
from channels.generic.http import AsyncHttpConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from django import http
from django.conf import settings
from django.views import View
from websockets.asyncio.client import ClientConnection

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
                nextjs_response_headers = [
                    (name.encode(), value.encode())
                    for name, value in response.headers.items()
                    if name.lower() in ["content-type", "set-cookie"]
                ]

                await self.send_headers(headers=nextjs_response_headers)
                async for data in response.content.iter_any():
                    await self.send_body(data, more_body=True)
                await self.send_body(b"", more_body=False)


class NextJSProxyWebsocketConsumer(AsyncWebsocketConsumer):
    """
    Manages WebSocket connections and proxies messages between the client (browser)
    and the Next.js development server.

    This consumer is essential for enabling real-time features like Hot Module
    Replacement (HMR) during development. It establishes a WebSocket connection
    to the Next.js server and relays messages back and forth, allowing for
    seamless updates in the browser when code changes are detected.

    Note: This consumer is intended for use in development environments only.
    """

    nextjs_connection: Optional[ClientConnection]
    nextjs_listener_task: Optional[asyncio.Task]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not settings.DEBUG:
            raise NextJSImproperlyConfigured("This proxy is for development only.")
        self.nextjs_connection = None
        self.nextjs_listener_task = None

    async def connect(self):
        nextjs_websocket_url = f"ws://{urlparse(NEXTJS_SERVER_URL).netloc}{self.scope['path']}"
        try:
            self.nextjs_connection = await websockets.connect(nextjs_websocket_url)
        except:
            await self.close()
            raise
        self.nextjs_listener_task = asyncio.create_task(self._receive_from_nextjs_server())
        await self.accept()

    async def _receive_from_nextjs_server(self):
        """
        Listens for messages from the Next.js development server and forwards them to the browser.
        """
        try:
            async for message in self.nextjs_connection:
                if isinstance(message, bytes):
                    await self.send(bytes_data=message)
                elif isinstance(message, str):
                    await self.send(text_data=message)
        except websockets.ConnectionClosedError:
            await self.close()

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handles incoming messages from the browser and forwards them to the Next.js development server.
        """
        data = text_data or bytes_data
        if not data:
            return
        try:
            await self.nextjs_connection.send(data)
        except websockets.ConnectionClosed:
            await self.close()

    async def disconnect(self, close_code):
        """
        Performs cleanup when the WebSocket connection is closed, either by the browser or by us.
        """

        if self.nextjs_listener_task:
            self.nextjs_listener_task.cancel()
            self.nextjs_listener_task = None

        if self.nextjs_connection:
            await self.nextjs_connection.close()
            self.nextjs_connection = None


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
        headers = {}
        for header in ["Cookie", "User-Agent"]:
            if header in request.headers:
                headers[header] = request.headers[header]

        urllib_response = urllib.request.urlopen(urllib.request.Request(url, headers=headers))

        return http.StreamingHttpResponse(
            self._iter_content(urllib_response), headers={"Content-Type": urllib_response.headers.get("Content-Type")}
        )

    def _iter_content(self, urllib_response: HTTPResponse):
        while True:
            chunk = urllib_response.read(urllib_response.length or 1)
            if not chunk:
                urllib_response.close()
                break
            yield chunk
