import aiohttp
import requests
from channels.generic.http import AsyncHttpConsumer
from django import http
from django.conf import settings
from django.views import View

from nextjs.app_settings import NEXTJS_SERVER_URL
from nextjs.exceptions import NextJSImproperlyConfigured


class NextJSProxyConsumer(AsyncHttpConsumer):
    """
    Proxies /next..., /_next..., /__nextjs... requests to Next.js server in development environment.

    - This is an async consumer for django channels.
    - Supports streaming response.
    """
    async def handle(self, body):
        if not settings.DEBUG:
            raise NextJSImproperlyConfigured("This proxy is for development only.")
        url = NEXTJS_SERVER_URL + self.scope["path"] + "?" + self.scope["query_string"].decode()
        original_headers = {k.decode(): v.decode() for k, v in self.scope["headers"]}
        headers = {}
        if "cookie" in original_headers:
            headers["cookie"] = original_headers["cookie"]
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

        if request.META.get("HTTP_ACCEPT", None) == "text/event-stream":
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
