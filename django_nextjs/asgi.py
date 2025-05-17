import typing

import aiohttp
from django.conf import settings

# https://github.com/encode/starlette/blob/b9db010d49cfa33d453facde56e53a621325c720/starlette/types.py
Scope = typing.MutableMapping[str, typing.Any]
Message = typing.MutableMapping[str, typing.Any]
Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Message], typing.Awaitable[None]]
ASGIApp = typing.Callable[[Scope, Receive, Send], typing.Awaitable[None]]


class DjangoNextjsASGIMiddleware:
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

    def __init__(self, inner_app: ASGIApp, *, nextjs_proxy_paths: typing.Optional[list[str]] = None) -> None:
        from django_nextjs.proxy import NextJSProxyHttpConsumer, NextJSProxyWebsocketConsumer

        self.inner_app = inner_app
        self.nextjs_proxy_paths: list[str] = nextjs_proxy_paths or ["/_next", "/__next", "/next"]
        # Pre-create ASGI callables for the consumers
        self.nextjs_proxy_http_consumer = NextJSProxyHttpConsumer.as_asgi()
        self.nextjs_proxy_ws_consumer = NextJSProxyWebsocketConsumer.as_asgi()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:

        # --- Lifespan Handling ---
        if scope["type"] == "lifespan":
            # Handle lifespan events (startup/shutdown)
            return await self._handle_lifespan(scope, receive, send)

        # --- Next.js Route Handling (DEBUG mode only) ---
        elif settings.DEBUG:
            path = scope.get("path", "")
            if any(path.startswith(prefix) for prefix in self.nextjs_proxy_paths):
                if scope["type"] == "http":
                    return await self.nextjs_proxy_http_consumer(scope, receive, send)
                elif scope["type"] == "websocket":
                    return await self.nextjs_proxy_ws_consumer(scope, receive, send)

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
