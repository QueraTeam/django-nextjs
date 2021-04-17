import aiohttp
import requests
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.template.loader import render_to_string
from .app_settings import NEXTJS_SERVER_URL


def _nextjs_html_to_django_response(html: str):
    extra_head = render_to_string("nextjs/extra_head.html")
    html = html.replace("</head>", extra_head + "</head>", 1)

    return HttpResponse(html)


def render_nextjs_page_sync(request: WSGIRequest) -> HttpResponse:
    page = request.path_info.lstrip("/")
    params = {k: request.GET.getlist(k) for k in request.GET.keys()}

    response = requests.get(
        f"{NEXTJS_SERVER_URL}/{page}", params=params, cookies=request.COOKIES
    )
    html = response.text

    return _nextjs_html_to_django_response(html)


async def render_nextjs_page_async(request: WSGIRequest) -> HttpResponse:
    page = request.path_info.lstrip("/")
    params = [(k, v) for k in request.GET.keys() for v in request.GET.getlist(k)]

    async with aiohttp.ClientSession(headers={"cookie": request.META["HTTP_COOKIE"]}) as session:
        async with session.get(f"{NEXTJS_SERVER_URL}/{page}", params=params) as response:
            html = await response.text()

    return _nextjs_html_to_django_response(html)
