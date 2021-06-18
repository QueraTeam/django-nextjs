import aiohttp
import requests
from django.conf import settings
from django.http import HttpRequest
from django.middleware.csrf import get_token as get_csrf_token
from django.template.loader import render_to_string

from .app_settings import NEXTJS_SERVER_URL


def _nextjs_html_to_django_response(html: str, extra_head: str = "") -> str:
    extra_head = render_to_string("nextjs/extra_head.html") + extra_head
    html = html.replace("</head>", extra_head + "</head>", 1)
    return html


def render_nextjs_page_sync(request: HttpRequest, extra_head: str = "") -> str:
    page = request.path_info.lstrip("/")
    params = {k: request.GET.getlist(k) for k in request.GET.keys()}

    response = requests.get(
        f"{NEXTJS_SERVER_URL}/{page}", params=params, cookies=request.COOKIES
    )
    html = response.text

    return _nextjs_html_to_django_response(html, extra_head)


async def render_nextjs_page_async(request: HttpRequest, extra_head: str = "") -> str:
    page = request.path_info.lstrip("/")
    params = [(k, v) for k in request.GET.keys() for v in request.GET.getlist(k)]

    # Ensure we always send a CSRF cookie to Next.js server (if there is none in `request` object, generate one)
    # Reason: We are going to issue GraphQL POST requests to fetch data in NextJS getServerSideProps.
    #         If this is the first request of user, there is no CSRF cookie and request fails,
    #         since GraphQL uses POST even for data fetching.
    # Isn't this a vulnerability?
    # No, as long as getServerSideProps functions are side effect free
    # (i.e. dont use HTTP unsafe methods or GraphQL mutations).
    # https://docs.djangoproject.com/en/3.2/ref/csrf/#is-posting-an-arbitrary-csrf-token-pair-cookie-and-post-data-a-vulnerability
    cookies = request.COOKIES | {settings.CSRF_COOKIE_NAME: get_csrf_token(request)}

    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(f"{NEXTJS_SERVER_URL}/{page}", params=params) as response:
            html = await response.text()

    return _nextjs_html_to_django_response(html, extra_head)
