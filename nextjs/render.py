import aiohttp
import requests
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.template.loader import render_to_string
from .app_settings import NEXTJS_SERVER_URL


def _nextjs_html_to_django_response(html: str, extra_head: str = ""):
    extra_head = render_to_string("nextjs/extra_head.html") + extra_head
    html = html.replace("</head>", extra_head + "</head>", 1)

    return HttpResponse(html)


def render_nextjs_page_sync(request: WSGIRequest, extra_head: str = "") -> HttpResponse:
    page = request.path_info.lstrip("/")
    params = {k: request.GET.getlist(k) for k in request.GET.keys()}

    response = requests.get(
        f"{NEXTJS_SERVER_URL}/{page}", params=params, cookies=request.COOKIES
    )
    html = response.text

    return _nextjs_html_to_django_response(html, extra_head)


async def render_nextjs_page_async(request: WSGIRequest, extra_head: str = "") -> HttpResponse:
    page = request.path_info.lstrip("/")
    params = [(k, v) for k in request.GET.keys() for v in request.GET.getlist(k)]

    headers = {"cookie": request.META["HTTP_COOKIE"]} if "HTTP_COOKIE" in request.META else None
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(f"{NEXTJS_SERVER_URL}/{page}", params=params) as response:
            html = await response.text()

    return _nextjs_html_to_django_response(html, extra_head)
