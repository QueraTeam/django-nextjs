import asyncio
import functools
import typing
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urlparse

import aiohttp
import websockets
from django.conf import settings
from websockets import Data
from websockets.asyncio.client import ClientConnection

from django_nextjs.app_settings import DEV_PROXY_PATHS, NEXTJS_SERVER_URL
from django_nextjs.exceptions import NextJsImproperlyConfigured

# https://github.com/encode/starlette/blob/b9db010d49cfa33d453facde56e53a621325c720/starlette/types.py
Scope = typing.MutableMapping[str, typing.Any]
Message = typing.MutableMapping[str, typing.Any]
Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Message], typing.Awaitable[None]]
ASGIApp = typing.Callable[[Scope, Receive, Send], typing.Awaitable[None]]


class StopReceiving(Exception):
    pass


class NextJsProxyBase(ABC):
    scope: Scope
    send: Send

    def __init__(self):
        if not settings.DEBUG:
            raise NextJsImproperlyConfigured("This proxy is for development only.")

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        self.scope = scope
        self.send = send

        while True:
            message = await receive()
            try:
                await self.handle_message(message)
            except StopReceiving:
                return  # Exit cleanly

    @abstractmethod
    async def handle_message(self, message: Message): ...

    @classmethod
    def as_asgi(cls):
        """
        Return an ASGI v3 single callable that instantiates a consumer instance per scope.
        Similar in purpose to Django's as_view().
        """

        async def app(scope: Scope, receive: Receive, send: Send):
            consumer = cls()
            return await consumer(scope, receive, send)

        # take name and docstring from class
        functools.update_wrapper(app, cls, updated=())
        return app


class NextJsHttpProxy(NextJsProxyBase):
    """
    Manages HTTP requests and proxies them to the Next.js development server.

    This handler is responsible for forwarding HTTP requests received by the
    Django application to the Next.js development server. It ensures that
    headers and body content are correctly relayed, and the response from
    the Next.js server is streamed back to the client. This is primarily
    used in development to serve Next.js assets through Django's ASGI server.
    """

    def __init__(self):
        super().__init__()
        self.body = []

    async def handle_message(self, message: Message) -> None:
        if message["type"] == "http.request":
            self.body.append(message.get("body", b""))
            if not message.get("more_body", False):
                await self.handle_request(b"".join(self.body))
        elif message["type"] == "http.disconnect":
            raise StopReceiving

    async def handle_request(self, body: bytes):
        url = NEXTJS_SERVER_URL + self.scope["path"] + "?" + self.scope["query_string"].decode()
        headers = {k.decode(): v.decode() for k, v in self.scope["headers"]}

        if session := self.scope.get("state", {}).get(DjangoNextJsAsgiMiddleware.HTTP_SESSION_KEY):
            session_is_temporary = False
        else:
            # If the shared session is not available, we create a temporary session.
            # This is typically the case when the ASGI server does not support the lifespan protocol (e.g. Daphne).
            session = aiohttp.ClientSession()
            session_is_temporary = True

        try:
            async with session.get(url, data=body, headers=headers) as response:
                nextjs_response_headers = [
                    (name.encode(), value.encode())
                    for name, value in response.headers.items()
                    if name.lower() in ["content-type", "set-cookie"]
                ]

                await self.send(
                    {"type": "http.response.start", "status": response.status, "headers": nextjs_response_headers}
                )
                async for data in response.content.iter_any():
                    await self.send({"type": "http.response.body", "body": data, "more_body": True})
                await self.send({"type": "http.response.body", "body": b"", "more_body": False})
        finally:
            if session_is_temporary:
                await session.close()


class NextJsWebSocketProxy(NextJsProxyBase):
    """
    Manages WebSocket connections and proxies messages between the client (browser)
    and the Next.js development server.

    This handler is essential for enabling real-time features like Hot Module
    Replacement (HMR) during development. It establishes a WebSocket connection
    to the Next.js server and relays messages back and forth, allowing for
    seamless updates in the browser when code changes are detected.
    """

    nextjs_connection: Optional[ClientConnection]
    nextjs_listener_task: Optional[asyncio.Task]

    def __init__(self):
        super().__init__()
        self.nextjs_connection = None
        self.nextjs_listener_task = None

    async def handle_message(self, message: Message) -> None:
        if message["type"] == "websocket.connect":
            await self.connect()
        elif message["type"] == "websocket.receive":
            if not self.nextjs_connection:
                await self.send({"type": "websocket.close"})
            elif data := message.get("text", message.get("bytes")):
                await self.receive(self.nextjs_connection, data=data)
        elif message["type"] == "websocket.disconnect":
            await self.disconnect()
            raise StopReceiving

    async def connect(self):
        nextjs_websocket_url = f"ws://{urlparse(NEXTJS_SERVER_URL).netloc}{self.scope['path']}"
        try:
            self.nextjs_connection = await websockets.connect(nextjs_websocket_url)
        except:
            await self.send({"type": "websocket.close"})
            raise
        self.nextjs_listener_task = asyncio.create_task(self._receive_from_nextjs_server(self.nextjs_connection))
        await self.send({"type": "websocket.accept"})

    async def _receive_from_nextjs_server(self, nextjs_connection: ClientConnection):
        """
        Listens for messages from the Next.js development server and forwards them to the browser.
        """
        try:
            async for message in nextjs_connection:
                if isinstance(message, bytes):
                    await self.send({"type": "websocket.send", "bytes": message})
                elif isinstance(message, str):
                    await self.send({"type": "websocket.send", "text": message})
        except websockets.ConnectionClosedError:
            await self.send({"type": "websocket.close"})

    async def receive(self, nextjs_connection: ClientConnection, data: Data):
        """
        Handles incoming messages from the browser and forwards them to the Next.js development server.
        """
        try:
            await nextjs_connection.send(data)
        except websockets.ConnectionClosed:
            await self.send({"type": "websocket.close"})

    async def disconnect(self):
        """
        Performs cleanup when the WebSocket connection is closed, either by the browser or by us.
        """

        if self.nextjs_listener_task:
            self.nextjs_listener_task.cancel()
            self.nextjs_listener_task = None

        if self.nextjs_connection:
            await self.nextjs_connection.close()
            self.nextjs_connection = None


class DjangoNextJsAsgiMiddleware:
    """
    ASGI middleware that integrates Django and Next.js applications.

    - Intercepts requests to Next.js paths (like '/_next', '/__next', '/next') in development
      mode and forwards them to the Next.js development server. This works as a transparent
      proxy, handling both HTTP requests and WebSocket connections (for Hot Module Replacement).

    - Manages an aiohttp ClientSession throughout the application lifecycle using the ASGI
      lifespan protocol. The session is created during application startup and properly closed
      during shutdown, ensuring efficient reuse of HTTP connections when communicating with the
      Next.js server.
    """

    HTTP_SESSION_KEY = "django_nextjs_http_session"

    def __init__(self, inner_app: ASGIApp) -> None:
        self.inner_app = inner_app

        if settings.DEBUG:
            # Pre-create ASGI callables for the consumers
            self.nextjs_http_proxy = NextJsHttpProxy.as_asgi()
            self.nextjs_websocket_proxy = NextJsWebSocketProxy.as_asgi()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:

        # --- Lifespan Handling ---
        if scope["type"] == "lifespan":
            # Handle lifespan events (startup/shutdown)
            return await self._handle_lifespan(scope, receive, send)

        # --- Next.js Route Handling (DEBUG mode only) ---
        elif settings.DEBUG:
            path = scope.get("path", "")
            if any(path.startswith(prefix) for prefix in DEV_PROXY_PATHS):
                if scope["type"] == "http":
                    return await self.nextjs_http_proxy(scope, receive, send)
                elif scope["type"] == "websocket":
                    return await self.nextjs_websocket_proxy(scope, receive, send)

        # --- Default Handling ---
        return await self.inner_app(scope, receive, send)

    async def _handle_lifespan(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Handle the lifespan protocol for the ASGI application.
        This is where we can manage the lifecycle of the application.

        https://asgi.readthedocs.io/en/latest/specs/lifespan.html
        """

        async def lifespan_receive() -> Message:
            message = await receive()
            if message["type"] == "lifespan.startup" and "state" in scope:
                # Create a new aiohttp ClientSession and store it in the scope's state.
                # This session will be used for making HTTP requests to the Next.js server
                # during the application's lifetime.
                scope["state"][self.HTTP_SESSION_KEY] = aiohttp.ClientSession()
            return message

        async def lifespan_send(message: Message) -> None:
            if message["type"] == "lifespan.shutdown.complete" and "state" in scope:
                # Clean up resources after inner app shutdown is complete
                http_session: typing.Optional[aiohttp.ClientSession] = scope["state"].get(self.HTTP_SESSION_KEY)
                if http_session:
                    await http_session.close()
            await send(message)

        try:
            await self.inner_app(scope, lifespan_receive, lifespan_send)
        except:
            # The underlying app has not implemented the lifespan protocol, so we run our own implementation.
            while True:
                lifespan_message = await lifespan_receive()
                if lifespan_message["type"] == "lifespan.startup":
                    await lifespan_send({"type": "lifespan.startup.complete"})
                elif lifespan_message["type"] == "lifespan.shutdown":
                    await lifespan_send({"type": "lifespan.shutdown.complete"})
                    return
