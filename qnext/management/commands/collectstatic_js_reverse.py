import json
import os

from django.conf import settings
from django.urls import get_resolver
from django_js_reverse.core import generate_json
from django_js_reverse.management.commands.collectstatic_js_reverse import Command as OriginalCommand

from qnext.app_settings import NEXTJS_REVERSE_PATH


class Command(OriginalCommand):
    """
    Extends the original collectstatic_js_reverse command from django_js_reverse.
    After generating `reverse.js`, generates a `reverse.json` file for Next.js app.
    """

    def handle(self, *args, **options):
        super().handle(self, *args, **options)
        if not os.path.exists(NEXTJS_REVERSE_PATH):
            os.makedirs(NEXTJS_REVERSE_PATH)

        json_file_path = os.path.join(NEXTJS_REVERSE_PATH, "reverse.json")

        urlconf = getattr(settings, "ROOT_URLCONF", None)
        default_urlresolver = get_resolver(urlconf)
        content = json.dumps(generate_json(default_urlresolver))
        with open(json_file_path, "w") as fp:
            fp.write(content)
        self.stdout.write("json file written to %s" % json_file_path)
