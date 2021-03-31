import requests
from django import http
from django.http import Http404
from django.views import View
from django.conf import settings

from .app_settings import NEXTJS_SERVER_URL


class NextJSProxy(View):
    """
    Proxies /next..., /_next..., /__nextjs... requests to Next.js server.
    Source: https://github.com/yourlabs/djnext/blob/master/src/djnext/views.py
    """

    development_only = False

    def dispatch(self, request, *args, **kwargs):
        if self.development_only and not settings.DEBUG:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
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
