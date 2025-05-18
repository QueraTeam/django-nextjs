import logging
import urllib.request
from http.client import HTTPResponse

from django import http
from django.conf import settings
from django.views import View

from django_nextjs.app_settings import NEXTJS_SERVER_URL
from django_nextjs.asgi import NextJSHttpProxy, NextJSWebsocketProxy
from django_nextjs.exceptions import NextJSImproperlyConfigured

logger = logging.getLogger(__name__)


class NextJSProxyHttpConsumer(NextJSHttpProxy):
    @classmethod
    def as_asgi(cls):
        # Use "logging" instead of "warnings" module because of this issue:
        # https://github.com/django/daphne/issues/352
        logger.warning(
            "NextJSProxyHttpConsumer is deprecated and will be removed in the next major release. "
            "Use DjangoNextjsASGIMiddleware from django_nextjs.asgi instead.",
        )
        return super().as_asgi()


class NextJSProxyWebsocketConsumer(NextJSWebsocketProxy):
    @classmethod
    def as_asgi(cls):
        # Use "logging" instead of "warnings" module because of this issue:
        # https://github.com/django/daphne/issues/352
        logger.warning(
            "NextJSProxyWebsocketConsumer is deprecated and will be removed in the next major release. "
            "Use DjangoNextjsASGIMiddleware from django_nextjs.asgi instead.",
        )
        return super().as_asgi()


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
