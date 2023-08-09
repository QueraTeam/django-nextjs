import pytest
from django.test import RequestFactory
from django_nextjs.proxy import NextJSProxyView
from django_nextjs.exceptions import NextJSImproperlyConfigured
from django.test import RequestFactory
from django.conf import settings


def test_dispatch_raises_exception_when_not_in_debug_mode(rf: RequestFactory):
    settings.DEBUG = False

    request = rf.get("/test")
    view = NextJSProxyView.as_view()
    with pytest.raises(NextJSImproperlyConfigured):
        view(request)


def test_(rf: RequestFactory):
    settings.DEBUG = True

    request = rf.get("/test")
    view = NextJSProxyView.as_view()

    # TODO:
