from http.cookies import Morsel
from typing import Dict, Tuple, Union
from urllib.parse import quote

import aiohttp
from asgiref.sync import sync_to_async
from django.conf import settings
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.middleware.csrf import get_token as get_csrf_token
from django.template.loader import render_to_string
from multidict import MultiMapping

from .app_settings import ENSURE_CSRF_TOKEN, NEXTJS_SERVER_URL
from .utils import filter_mapping_obj

morsel = Morsel()


def _get_render_context(html: str, extra_context: Union[Dict, None] = None):
    a = html.find("<head>")
    b = html.find('</head><body id="__django_nextjs_body"', a)
    c = html.find('<div id="__django_nextjs_body_begin"', b)
    d = html.find('<div id="__django_nextjs_body_end"', c)

    if any(i == -1 for i in (a, b, c, d)):
        return None

    return {
        **(extra_context or {}),
        "django_nextjs__": {
            "section1": html[: a + len("<head>")],
            "section2": html[a + len("<head>") : b],
            "section3": html[b:c],
            "section4": html[c:d],
            "section5": html[d:],
        },
    }


def _get_nextjs_request_cookies(request: HttpRequest):
    """
    Ensure we always send a CSRF cookie to Next.js server (if there is none in `request` object, generate one)
    """
    unreserved_cookies = {k: v for k, v in request.COOKIES.items() if k and not morsel.isReservedKey(k)}
    if ENSURE_CSRF_TOKEN is True and settings.CSRF_COOKIE_NAME not in unreserved_cookies:
        unreserved_cookies[settings.CSRF_COOKIE_NAME] = get_csrf_token(request)
    return unreserved_cookies


def _get_nextjs_request_headers(request: HttpRequest, headers: Union[Dict, None] = None):
    # These headers are used by NextJS to indicate if a request is expecting a full HTML
    # response, or an RSC response.
    server_component_headers = filter_mapping_obj(
        request.headers,
        selected_keys=[
            "Rsc",
            "Next-Router-State-Tree",
            "Next-Router-Prefetch",
            "Next-Url",
            "Cookie",
            "Accept-Encoding",
        ],
    )

    return {
        "x-real-ip": request.headers.get("X-Real-Ip", "") or request.META.get("REMOTE_ADDR", ""),
        "user-agent": request.headers.get("User-Agent", ""),
        **server_component_headers,
        **(headers or {}),
    }


def _get_nextjs_response_headers(headers: MultiMapping[str]) -> Dict:
    return filter_mapping_obj(
        headers,
        selected_keys=[
            "Location",
            "Vary",
            "Content-Type",
            "Set-Cookie",
            "Link",
            "Cache-Control",
            "Connection",
            "Date",
            "Keep-Alive",
        ],
    )


async def _render_nextjs_page_to_string(
    request: HttpRequest,
    template_name: str = "",
    context: Union[Dict, None] = None,
    using: Union[str, None] = None,
    allow_redirects: bool = False,
    headers: Union[Dict, None] = None,
) -> Tuple[str, int, Dict[str, str]]:
    page_path = quote(request.path_info.lstrip("/"))
    params = [(k, v) for k in request.GET.keys() for v in request.GET.getlist(k)]

    # Get HTML from Next.js server
    async with aiohttp.ClientSession(
        cookies=_get_nextjs_request_cookies(request),
        headers=_get_nextjs_request_headers(request, headers),
    ) as session:
        async with session.get(
            f"{NEXTJS_SERVER_URL}/{page_path}", params=params, allow_redirects=allow_redirects
        ) as response:
            html = await response.text()
            response_headers = _get_nextjs_response_headers(response.headers)

    # Apply template rendering (HTML customization) if template_name is provided
    if template_name:
        render_context = _get_render_context(html, context)
        if render_context is not None:
            html = await sync_to_async(render_to_string)(
                template_name, context=render_context, request=request, using=using
            )
    return html, response.status, response_headers


async def render_nextjs_page_to_string(
    request: HttpRequest,
    template_name: str = "",
    context: Union[Dict, None] = None,
    using: Union[str, None] = None,
    allow_redirects: bool = False,
    headers: Union[Dict, None] = None,
):
    html, _, _ = await _render_nextjs_page_to_string(
        request,
        template_name,
        context,
        using=using,
        allow_redirects=allow_redirects,
        headers=headers,
    )
    return html


async def render_nextjs_page(
    request: HttpRequest,
    template_name: str = "",
    context: Union[Dict, None] = None,
    using: Union[str, None] = None,
    allow_redirects: bool = False,
    headers: Union[Dict, None] = None,
):
    content, status, response_headers = await _render_nextjs_page_to_string(
        request,
        template_name,
        context,
        using=using,
        allow_redirects=allow_redirects,
        headers=headers,
    )
    return HttpResponse(content=content, status=status, headers=response_headers)


async def stream_nextjs_page(
    request: HttpRequest,
    allow_redirects: bool = False,
    headers: Union[Dict, None] = None,
):
    """
    Stream a Next.js page response.
    This function is used to stream the response from a Next.js server.
    """
    page_path = quote(request.path_info.lstrip("/"))
    params = [(k, v) for k in request.GET.keys() for v in request.GET.getlist(k)]
    next_url = f"{NEXTJS_SERVER_URL}/{page_path}"

    session = aiohttp.ClientSession()

    try:
        nextjs_response = await session.get(
            next_url,
            params=params,
            allow_redirects=allow_redirects,
            cookies=_get_nextjs_request_cookies(request),
            headers=_get_nextjs_request_headers(request, headers)
        )
        response_headers = _get_nextjs_response_headers(nextjs_response.headers)

        async def stream_nextjs_response():
            try:
                async for chunk in nextjs_response.content.iter_any():
                    yield chunk
            finally:
                await nextjs_response.release()
                await session.close()

        return StreamingHttpResponse(
            stream_nextjs_response(),
            status=nextjs_response.status,
            headers=response_headers,
        )
    except:
        await session.close()
        raise
