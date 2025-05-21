# Django-Next.js

[![Tests status](https://github.com/QueraTeam/django-nextjs/workflows/tests/badge.svg)](https://github.com/QueraTeam/django-nextjs/actions)
[![PyPI version](https://img.shields.io/pypi/v/django-nextjs.svg)](https://pypi.org/project/django-nextjs/)
![PyPI downloads](https://img.shields.io/pypi/dm/django-nextjs.svg)
[![License: MIT](https://img.shields.io/github/license/QueraTeam/django-nextjs.svg)](https://github.com/QueraTeam/django-nextjs/blob/master/LICENSE)
[![Code style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Integrate Next.js into your Django project,
allowing Django and Next.js pages to work together seamlessly.

## Compatibility

- **Python**: 3.9, 3.10, 3.11, 3.12, 3.13
- **Django**: 4.2, 5.0, 5.1, 5.2

## Why django-nextjs?

django-nextjs is designed for projects
that need both Django pages (usually rendered by Django templates) and Next.js pages. Some scenarios:

- You want to add some Next.js pages to an existing Django project.
- You want to migrate your frontend to Next.js, but since the project is large, you want to do it gradually.

If this sounds like you, **this package is the perfect fit**. ✅

However, if you’re starting a new project and intend to use Django purely as an API backend with Next.js as a standalone frontend, you don’t need this package.
Simply run both servers and configure your public web server to route requests to Next.js; this provides a more straightforward setup.

## How it works

**django-nextjs** creates a seamless bridge between Django and Next.js. When a user opens a page, Django receives the initial request, queries the Next.js server for the HTML response, and returns it to the user.
After opening a Next.js page, the user can navigate to other Next.js pages without any additional requests to Django (the Next.js server handles the routing).

In development, Django also acts as the reverse proxy, simplifying the setup and eliminating the need for Nginx during development.

![How it works in production](.github/assets/how-it-works-production.webp)

## Getting started

Install the latest version from PyPI:

```shell
pip install django-nextjs
```

Add `django_nextjs` to `INSTALLED_APPS` in your Django settings:

```python
INSTALLED_APPS = [
    ...
    "django_nextjs",
]
```

Configure your project's `asgi.py` with `NextJsMiddleware` as shown below:

```python
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django_asgi_app = get_asgi_application()

from django_nextjs.asgi import NextJsMiddleware

application = NextJsMiddleware(django_asgi_app)
```

The middleware automatically handles routing for Next.js assets and API requests, and supports WebSocket connections for fast refresh to work properly.

You can use `NextJsMiddleware` with any ASGI application.
For example, you can use it with `ProtocolTypeRouter`
if you are using [Django Channels](https://channels.readthedocs.io/en/latest/):

```python
application = NextJsMiddleware(
    ProtocolTypeRouter(
        {
            "http": django_asgi_app,
            "websocket": my_websocket_handler,
            # ...
        }
    )
)
```

If you're not using ASGI, add the following path to the beginning of `urls.py`:

```python
urlpatterns = [
    path("", include("django_nextjs.urls")),
    ...
]
```

> [!IMPORTANT]
> Using ASGI is **required**
> for [fast refresh](https://nextjs.org/docs/architecture/fast-refresh)
> to work properly.
> Without it, you'll need to manually refresh your browser
> to see changes during development.
>
> To run your ASGI application, you can use an ASGI server
> such as [Daphne](https://github.com/django/daphne)
> or [Uvicorn](https://www.uvicorn.org/).

> [!WARNING]
> The `NextJSProxyHttpConsumer` and `NextJSProxyWebsocketConsumer` classes that were previously used for setup still exist and work, but they are deprecated and will be removed in the next major release. Please use the `NextJsMiddleware` approach described above.

## Setup Next.js URLs in production

In production, use a reverse proxy like Nginx or Caddy.

| URL                 | Action                                                      |
|---------------------|-------------------------------------------------------------|
| `/_next/static/...` | Serve `NEXTJS_PATH/.next/static` directory                  |
| `/_next/...`        | Proxy to the Next.js server (e.g., `http://127.0.0.1:3000`) |
| `/next/...`         | Serve `NEXTJS_PATH/public/next` directory                   |

Example Nginx configuration:

```conf
location /_next/static/ {
    alias NEXTJS_PATH/.next/static/;
    expires max;
    add_header Cache-Control "public";
}
location /_next/ {
    proxy_pass  http://127.0.0.1:3000;
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
location /next/ {
    alias NEXTJS_PATH/public/next/;
    expires max;
    add_header Cache-Control "public";
}
```

## Usage

Start the Next.js server using `npm run dev` (development) or `npm run start` (production).

Define Django URLs for your Next.js pages:

```python
from django_nextjs.views import nextjs_page

urlpatterns = [
    path("/my/page", nextjs_page(), name="my_page"),

    # With App Router streaming (recommended)
    path("/other/page", nextjs_page(stream=True), name="other_page"),
]
```

### The `stream` parameter

If you're using the [Next.js App Router](https://nextjs.org/docs/app), you can enable streaming by setting the `stream` parameter to `True` in the `nextjs_page` function. This allows the HTML response to be streamed directly from the Next.js server to the client. This approach is particularly useful for server-side rendering with streaming support to display an [instant loading state](https://nextjs.org/docs/app/building-your-application/routing/loading-ui-and-streaming#instant-loading-states) from the Next.js server while the content of a route segment loads.

Currently, the default value for this parameter
is set to `False` for backward compatibility.
It will default to `True` in the next major release.

## Customizing the HTML response

You can modify the HTML code that Next.js returns in your Django code.

> [!WARNING]
> This feature is not compatible with the Next.js App Router, and to use it,
> you need to set the `stream` parameter to `False` in the `nextjs_page` function.
> Because of these limitations, we do not recommend using this feature.
> For more details, please refer to [this GitHub issue](https://github.com/QueraTeam/django-nextjs/issues/22).

This is a common use case for avoiding duplicate code for the navbar and footer if you are using both Next.js and Django templates.
Without it, you would have to write and maintain two separate versions
of your navbar and footer (a Django template version and a Next.js version).
However, you can simply create a Django template for your navbar and insert its code
at the beginning of the `<body>` tag in the HTML returned by Next.js.

To enable this feature, you need to customize the Next.js `pages/_document` file and make the following adjustments:

- Add `id="__django_nextjs_body"` as the first attribute of the `<body>` element.
- Add `<div id="__django_nextjs_body_begin" />` as the first element inside `<body>`.
- Add `<div id="__django_nextjs_body_end" />` as the last element inside `<body>`.

Read
[this doc](https://nextjs.org/docs/pages/building-your-application/routing/custom-document)
and customize your Next.js document:

```jsx
// pages/_document.jsx (or .tsx)
...
<body id="__django_nextjs_body">
  <div id="__django_nextjs_body_begin" />
  <Main />
  <NextScript />
  <div id="__django_nextjs_body_end" />
</body>
...
```

Write a Django template that extends `django_nextjs/document_base.html`:

```django
{% extends "django_nextjs/document_base.html" %}


{% block head %}
  <!-- ... the content you want to place at the beginning of "head" tag ... -->
  {{ block.super }}
  <!-- ... the content you want to place at the end of "head" tag ... -->
{% endblock %}


{% block body %}
  ... the content you want to place at the beginning of "body" tag ...
  ... e.g. include the navbar template ...
  {{ block.super }}
  ... the content you want to place at the end of "body" tag ...
  ... e.g. include the footer template ...
{% endblock %}
```

Pass the template name to `nextjs_page`:

```python
from django_nextjs.views import nextjs_page

urlpatterns = [
    path("/my/page", nextjs_page(template_name="path/to/template.html"), name="my_page"),
]
```

## Notes

- Place Next.js [public](https://nextjs.org/docs/app/api-reference/file-conventions/public-folder) files in the `public/next` subdirectory.
- Ensure all your middlewares are [async-capable](https://docs.djangoproject.com/en/dev/topics/http/middleware/#asynchronous-support).
- Set `APPEND_SLASH = False` in `settings.py` to avoid redirect loops, and don't add trailing slashes to Next.js paths.
- Implement an API to pass data between Django and Next.js.
  You can use Django REST Framework or GraphQL.
- This package doesn't start Next.js - you'll need to run it separately.

## Settings

You can configure `django-nextjs` using the `NEXTJS_SETTINGS` dictionary in your Django settings file.
The default settings are:

```python
NEXTJS_SETTINGS = {
    "nextjs_server_url": "http://127.0.0.1:3000",
    "ensure_csrf_token": True,
    "public_subdirectory": "/next",
}
```

### `nextjs_server_url`

The URL of the Next.js server (started by `npm run dev` or `npm run start`)

### `ensure_csrf_token`

If the user does not have a CSRF token, ensure that one is generated and included in the initial request to the Next.js server by calling Django's `django.middleware.csrf.get_token`. If `django.middleware.csrf.CsrfViewMiddleware` is installed, the initial response will include a `Set-Cookie` header to persist the CSRF token value on the client. This behavior is enabled by default.

> [!TIP]
> **The use case for this option**
>
> You may need to issue GraphQL POST requests to fetch data in Next.js `getServerSideProps`. If this is the user's first request, there will be no CSRF cookie, causing the request to fail since GraphQL uses POST even for data fetching.
> In this case, this option solves the issue,
> and as long as `getServerSideProps` functions are side-effect free (i.e., they don't use HTTP unsafe methods or GraphQL mutations), it should be fine from a security perspective. Read more [here](https://docs.djangoproject.com/en/3.2/ref/csrf/#is-posting-an-arbitrary-csrf-token-pair-cookie-and-post-data-a-vulnerability).

### `public_subdirectory`

Use this option to set a custom path instead of `/next` inside the Next.js
[`public` directory](https://nextjs.org/docs/app/api-reference/file-conventions/public-folder).
For example, you can set this option to `/static-next`
and place the Next.js static files in the `public/static-next` directory.
You should also update the production reverse proxy configuration accordingly.

## Contributing

We welcome contributions from the community! Here's how to get started:

1. Install development dependencies: `pip install -e '.[dev]'`
2. Set up pre-commit hooks: `pre-commit install`
3. Make your changes and submit a pull request.

Love django-nextjs? Give a star 🌟  on GitHub to help the project grow!

## License

MIT - See [LICENSE](https://github.com/QueraTeam/django-nextjs/blob/main/LICENSE) for details.
