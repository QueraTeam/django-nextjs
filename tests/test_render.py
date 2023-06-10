from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.test import RequestFactory
from django.utils.datastructures import MultiValueDict

from django_nextjs.render import _get_render_context, render_nextjs_page_async


def test_get_render_context_empty_html():
    assert _get_render_context("") is None


def test_get_render_context_html_without_children():
    assert _get_render_context("<html></html>") is None


def test_get_render_context_html_with_empty_sections():
    assert _get_render_context("<html><head></head><body></body></html>") is None


def test_get_render_context_html_with_incomplete_sections():
    assert (
        _get_render_context(
            """<html><head></head><body><div id="__django_nextjs_body_begin"/>
            <div id="__django_nextjs_body_end"/></body></html>"""
        )
        is None
    )


def test_get_render_context_html_with_sections_and_content():
    html = """<html><head><link/></head><body id="__django_nextjs_body"><div id="__django_nextjs_body_begin"/><div id="__django_nextjs_body_end"/></body></html>"""
    expected_context = {
        "django_nextjs__": {
            "section1": "<html><head>",
            "section2": "<link/>",
            "section3": '</head><body id="__django_nextjs_body">',
            "section4": '<div id="__django_nextjs_body_begin"/>',
            "section5": '<div id="__django_nextjs_body_end"/></body></html>',
        }
    }
    assert _get_render_context(html) == expected_context

    context = {"extra_context": "content"}
    assert _get_render_context(html, context) == {**expected_context, **context}


@pytest.mark.asyncio
async def test_render_nextjs_page_to_string_async(rf: RequestFactory):
    path = "random/path"
    params = MultiValueDict({"name": ["Adrian", "Simon"], "position": ["Developer"]})
    request = rf.get(f"/{path}", data=params)
    nextjs_response = "<html><head></head><body></body></html>"
    nextjs_server_url = "http://127.0.0.1:3000"

    with patch("aiohttp.ClientSession") as mock_session:
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(return_value=nextjs_response)
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.headers = {"Location": "target_value", "unimportant": ""}
            mock_session.return_value.__aenter__ = AsyncMock(return_value=MagicMock(get=mock_get))

            http_response = await render_nextjs_page_async(request, allow_redirects=True, headers={"extra": "headers"})

            assert http_response.content == nextjs_response.encode()
            assert http_response.status_code == 200
            assert http_response.has_header("Location")
            assert http_response.has_header("unimportant") is False

            # Arguments passed to aiohttp.ClientSession.get
            args, kwargs = mock_get.call_args
            url = args[0]
            assert url == f"{nextjs_server_url}/{path}"
            assert [(k, v) for k in params.keys() for v in params.getlist(k)] == kwargs["params"]
            assert kwargs["allow_redirects"] is True

        args, kwargs = mock_session.call_args
        assert "csrftoken" in kwargs["cookies"]
        assert kwargs["headers"] == {"user-agent": "", "x-real-ip": "127.0.0.1", "extra": "headers"}
