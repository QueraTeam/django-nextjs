import os

from django.conf import settings

NEXTJS_SETTINGS = getattr(settings, "NEXTJS_SETTINGS", {})

NEXTJS_SERVER_URL = NEXTJS_SETTINGS.get("nextjs_server_url", "http://127.0.0.1:3000")
ENSURE_CSRF_TOKEN = NEXTJS_SETTINGS.get("ensure_csrf_token", True)
PUBLIC_SUBDIRECTORY = NEXTJS_SETTINGS.get("public_subdirectory", "/next")
