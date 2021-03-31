import os

from django.conf import settings

QNEXT_SETTINGS = getattr(settings, "QNEXT_SETTINGS", {})

NEXTJS_SERVER_URL = QNEXT_SETTINGS.get("nextjs_server_url", "http://127.0.0.1:3000")
NEXTJS_REVERSE_PATH = QNEXT_SETTINGS.get("nextjs_reverse_path", os.path.join(settings.BASE_DIR, "next/reverse"))
