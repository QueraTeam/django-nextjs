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


def _nextjs_html_to_django_response_sync(request: HttpRequest, html: str, extra_head: str = "", context=None) -> str:
    head_append = render_to_string("nextjs/head_append.html", context=context, request=request) + extra_head
    body_prepend = render_to_string("nextjs/body_prepend.html", context=context, request=request)
    body_append = render_to_string("nextjs/body_append.html", context=context, request=request)
    html = html.replace("</head>", head_append + "</head>", 1).replace(
        """<div id="__next">""", f"""{body_prepend}<div id="__next">""", 1
    ).replace("</body>", body_append + "</body>", 1)
    return html


def render_nextjs_page_sync(request: HttpRequest, extra_head: str = "", context=None) -> str:
    page = request.path_info.lstrip("/")
    params = {k: request.GET.getlist(k) for k in request.GET.keys()}

    response = requests.get(
        f"{NEXTJS_SERVER_URL}/{page}",
        params=params,
        cookies=_get_cookies(request),
        headers={"user-agent": request.META.get("HTTP_USER_AGENT", "")},
    )
    html = response.text

    return _nextjs_html_to_django_response_sync(request, html, extra_head, context)


async def _nextjs_html_to_django_response_async(request: HttpRequest, html: str, extra_head: str = "", context=None) -> str:
    head_append = (await sync_to_async(render_to_string)("nextjs/head_append.html", context=context, request=request)) + extra_head
    body_prepend = await sync_to_async(render_to_string)("nextjs/body_prepend.html", context=context, request=request)
    body_append = await sync_to_async(render_to_string)("nextjs/body_append.html", context=context, request=request)
    html = html.replace("</head>", head_append + "</head>", 1).replace(
        """<div id="__next">""", f"""{body_prepend}<div id="__next">""", 1
    ).replace("</body>", body_append + "</body>", 1)
    return html


async def render_nextjs_page_async(request: HttpRequest, extra_head: str = "", context=None) -> str:
    page = request.path_info.lstrip("/")
    params = [(k, v) for k in request.GET.keys() for v in request.GET.getlist(k)]

    async with aiohttp.ClientSession(
        cookies=_get_cookies(request),
        headers={"user-agent": request.META.get("HTTP_USER_AGENT", "")}
    ) as session:
        async with session.get(f"{NEXTJS_SERVER_URL}/{page}", params=params) as response:
            html = await response.text()

    return await _nextjs_html_to_django_response_async(request, html, extra_head, context)
