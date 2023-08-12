from django.contrib import admin
from django.urls import include, path

from django_nextjs.render import render_nextjs_page


async def nextjs_page(request):
    return await render_nextjs_page(request)


async def nextjs_page_with_template(request):
    return await render_nextjs_page(request, "index.html")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", nextjs_page),
    path("app", nextjs_page_with_template),
    path("app/second", nextjs_page_with_template),
    path("page", nextjs_page_with_template),
    path("page/second", nextjs_page_with_template),
    path("", include("django_nextjs.urls")),
]
