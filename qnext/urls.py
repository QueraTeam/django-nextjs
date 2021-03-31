from django.urls import re_path
from .views import NextJSProxy

app_name = "qnext"
urlpatterns = [
    re_path(r"^(?:next|__nextjs).*$", NextJSProxy.as_view(development_only=True)),  # only in dev environment
    re_path(r"^_next/.*$", NextJSProxy.as_view()),  # both development and production
]
