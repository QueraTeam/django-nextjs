from django.conf import settings
from django.urls import re_path

from .proxy import NextJSProxyView

app_name = "nextjs"
urlpatterns = []

if settings.DEBUG:
    # only in dev environment
    urlpatterns.append(re_path(r"^(?:_next|__nextjs|next).*$", NextJSProxyView.as_view()))
