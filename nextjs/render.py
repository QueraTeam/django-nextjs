import aiohttp
import requests
from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import HttpRequest
from django.middleware.csrf import get_token as get_csrf_token
from django.template.loader import render_to_string

from .app_settings import NEXTJS_SERVER_URL


def _get_cookies(request):
    # Ensure we always send a CSRF cookie to Next.js server (if there is none in `request` object, generate one)
    # Reason: We are going to issue GraphQL POST requests to fetch data in NextJS getServerSideProps.
    #         If this is the first request of user, there is no CSRF cookie and request fails,
    #         since GraphQL uses POST even for data fetching.
    # Isn't this a vulnerability?
    # No, as long as getServerSideProps functions are side effect free
    # (i.e. dont use HTTP unsafe methods or GraphQL mutations).
    # https://docs.djangoproject.com/en/3.2/ref/csrf/#is-posting-an-arbitrary-csrf-token-pair-cookie-and-post-data-a-vulnerability
    return request.COOKIES | {settings.CSRF_COOKIE_NAME: get_csrf_token(request)}


def _nextjs_html_to_django_response_sync(request: HttpRequest, html: str, extra_head: str = "") -> str:
    append_head = render_to_string("nextjs/append_head.html") + extra_head
    prepend_body = render_to_string("nextjs/prepend_body.html", request=request)
    html = html.replace("</head>", append_head + "</head>", 1).replace(
        """<div id="__next">""", f"""{prepend_body}<div id="__next">""", 1
    )
    return html


def render_nextjs_page_sync(request: HttpRequest, extra_head: str = "") -> str:
    page = request.path_info.lstrip("/")
    params = {k: request.GET.getlist(k) for k in request.GET.keys()}

    response = requests.get(
        f"{NEXTJS_SERVER_URL}/{page}",
        params=params,
        cookies=_get_cookies(request),
        headers={"user-agent": request.META.get("HTTP_USER_AGENT", "")},
    )
    html = response.text

    return _nextjs_html_to_django_response_sync(request, html, extra_head)


async def _nextjs_html_to_django_response_async(request: HttpRequest, html: str, extra_head: str = "") -> str:
    append_head = (await sync_to_async(render_to_string)("nextjs/append_head.html", request=request)) + extra_head
    prepend_body = await sync_to_async(render_to_string)("nextjs/prepend_body.html", request=request)
    html = html.replace("</head>", append_head + "</head>", 1).replace(
        """<div id="__next">""", f"""{prepend_body}<div id="__next">""", 1
    )
    return html


async def render_nextjs_page_async(request: HttpRequest, extra_head: str = "") -> str:
    page = request.path_info.lstrip("/")
    params = [(k, v) for k in request.GET.keys() for v in request.GET.getlist(k)]

    async with aiohttp.ClientSession(
        cookies=_get_cookies(request),
        headers={"user-agent": request.META.get("HTTP_USER_AGENT", "")}
    ) as session:
        async with session.get(f"{NEXTJS_SERVER_URL}/{page}", params=params) as response:
            html = await response.text()

    return await _nextjs_html_to_django_response_async(request, html, extra_head)
