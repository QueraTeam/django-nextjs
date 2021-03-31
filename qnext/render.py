import json

import requests
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.template.loader import render_to_string
from .app_settings import NEXTJS_SERVER_URL


def render_nextjs_page(request: WSGIRequest, state: dict = None):
    page = request.path_info.lstrip("/")

    response = requests.get(
        f"{NEXTJS_SERVER_URL}/{page}", {"state": json.dumps(state or dict())}, cookies=request.COOKIES
    )
    html = response.text

    extra_head = render_to_string("qnext/extra_head.html")
    html = html.replace("</head>", extra_head + "</head>", 1)

    return HttpResponse(html)
