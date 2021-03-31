import os

from django.conf import settings

NEXTJS_SETTINGS = getattr(settings, "NEXTJS_SETTINGS", {})

NEXTJS_SERVER_URL = NEXTJS_SETTINGS.get("nextjs_server_url", "http://127.0.0.1:3000")
NEXTJS_REVERSE_PATH = NEXTJS_SETTINGS.get("nextjs_reverse_path", os.path.join(settings.BASE_DIR, "next/reverse"))
