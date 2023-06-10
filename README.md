# Django Next.js

[![](https://img.shields.io/pypi/v/django-nextjs.svg)](https://pypi.python.org/pypi/django-nextjs/)
[![](https://github.com/QueraTeam/django-nextjs/workflows/tests/badge.svg)](https://github.com/QueraTeam/django-nextjs/actions)
[![](https://img.shields.io/github/license/QueraTeam/django-nextjs.svg)](https://github.com/QueraTeam/django-nextjs/blob/master/LICENSE)
[![](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Next.js integration for Django projects.

So you want to use both Django and Next.js in your project. There are two scenarios:

1. You are starting a new project and you want to use Django as back-end and Next.js as front-end.
   Django only serves API requests. All front-end code lives in Next.js and you don't write any Django template.

   In this scenario you **don't need** this package (although you can use it).
   You simply start both Django and Next.js servers and point your public webserver to Next.js.

2. You need both Django templates and Next.js at the same time and those pages should easily link to each other.
   Maybe you have an existing Django project which has pages rendered by Django template
   and want some new pages in Next.js.
   Or you want to migrate your front-end to Next.js but since the project is large, you need to do it gradually.

   In this scenario, **this package is for you!**

## How does it work?

From a [comment on StackOverflow]:

> Run 2 ports on the same server. One for django (public facing)
> and one for Next.js (internal).
> Let django handle all web requests.
> For each request, query Next.js from django view to get HTML response.
> Return that exact HTML response from django view.

## Installation

- Install the latest version from PyPI.

  ```shell
  pip install django-nextjs
  ```

- Add `django_nextjs.apps.DjangoNextJSConfig` to `INSTALLED_APPS`.

- **In Development Environment:**

  - If you're using django channels (after Nextjs v12 you need this to be able to use hot-reload), add `NextJSProxyHttpConsumer` and `NextJSProxyWebsocketConsumer` to `asgi.py`:

    ```python
    import os

    from django.core.asgi import get_asgi_application
    from django.urls import re_path, path

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
    django_asgi_app = get_asgi_application()

    from channels.auth import AuthMiddlewareStack
    from channels.routing import ProtocolTypeRouter, URLRouter
    from django_nextjs.proxy import NextJSProxyHttpConsumer, NextJSProxyWebsocketConsumer

    from django.conf import settings

    # put your custom routes here if you need
    http_routes = [re_path(r"", django_asgi_app)]
    websocket_routers = []

    if settings.DEBUG:
        http_routes.insert(0, re_path(r"^(?:_next|__next|next).*", NextJSProxyHttpConsumer.as_asgi()))
        websocket_routers.insert(0, path("_next/webpack-hmr", NextJSProxyWebsocketConsumer.as_asgi()))


    application = ProtocolTypeRouter(
        {
            # Django's ASGI application to handle traditional HTTP and websocket requests.
            "http": URLRouter(http_routes),
            "websocket": AuthMiddlewareStack(URLRouter(websocket_routers)),
            # ...
        }
    )
    ```

  - Otherwise, add the following to the beginning of `urls.py`:

    ```python
    path("", include("django_nextjs.urls"))
    ```

- **In Production:**

  - Use a reverse proxy like nginx:

    | URL                 | Action                                     |
    | ------------------- | ------------------------------------------ |
    | `/_next/static/...` | Serve `NEXTJS_PATH/.next/static` directory |
    | `/_next/...`        | Proxy to `http://localhost:3000`           |
    | `/next/...`         | Serve `NEXTJS_PATH/public/next` directory  |

    Pass `x-real-ip` header when proxying `/_next/`:

    ```conf
    location /_next/ {
        proxy_set_header  x-real-ip $remote_addr;
        proxy_pass  http://127.0.0.1:3000;
    }
    ```

## Usage

Start Next.js server:

```shell
# Development:
$ npm run dev

# Production:
$ npm run build
$ npm run start
```

Develop your pages in Next.js.
Write a django URL and view for each page like this:

```python
# If you're using django channels
from django.http import HttpResponse
from django_nextjs.render import render_nextjs_page_async

async def jobs(request):
    return await render_nextjs_page_async(request)
```

```python
# If you're not using django channels
from django.http import HttpResponse
from django_nextjs.render import render_nextjs_page_sync

def jobs(request):
    return render_nextjs_page_sync(request)
```

## Customizing the HTML Response

You can modify the HTML code that Next.js returns in your Django code.

Avoiding duplicate code for the navbar and footer is a common use case
for this if you are using both Next.js and Django templates.
Without it, you would have to write and maintain two separate versions
of your navbar and footer (a Django template version and a Next.js version).
However, you can simply create a Django template for your navbar and insert its code
at the beginning of `<body>` tag returned from Next.js.

To enable this feature, you need to customize the document and root layout
in Next.js and make the following adjustments:

- Add `id="__django_nextjs_body"` as the first attribute of `<body>` element.
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

If you are using Next.js 13+, you also need to
[customize the root layout](https://nextjs.org/docs/app/api-reference/file-conventions/layout)
in `app` directory:

```jsx
// app/layout.jsx (or .tsx)
...
<body id="__django_nextjs_body" className={inter.className}>
  <div id="__django_nextjs_body_begin" />
  {children}
  <div id="__django_nextjs_body_end" />
</body>
...
```

Write a django template that extends `django_nextjs/document_base.html`:

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

Pass the template name to `render_nextjs_page_async` or `render_nextjs_page_sync`:

```python
# If you're using django channels
async def jobs(request):
    return await render_nextjs_page_async(request, "path/to/template.html")
```

```python
# If you're not using django channels
def jobs(request):
    return render_nextjs_page_sync(request, "path/to/template.html")
```

## Notes

- If you want to add a file to `public` directory of Next.js,
  that file should be in `public/next` subdirectory to work correctly.
- If you're using django channels, make sure all your middlewares are
  [async-capable](https://docs.djangoproject.com/en/dev/topics/http/middleware/#asynchronous-support).
- To avoid "Too many redirects" error, you may need to add `APPEND_SLASH = False` in your Django project's `settings.py`. Also, do not add `/` at the end of nextjs paths in `urls.py`.
- This package does not provide a solution for passing data from Django to Next.js. The Django Rest Framework, GraphQL, or similar solutions should still be used.
- The Next.js server will not be run by this package. You will need to run it yourself.

## Settings

Default settings:

```python
    NEXTJS_SETTINGS = {
        "nextjs_server_url": "http://127.0.0.1:3000",
    }
```

### `nextjs_server_url`

The URL of Next.js server (started by `npm run dev` or `npm run start`)

## Development

- Install development dependencies in your virtualenv with `pip install -e '.[dev]'`
- Install pre-commit hooks using `pre-commit install`.

## References

- https://github.com/yourlabs/djnext
- [comment on StackOverflow]

[comment on stackoverflow]: https://stackoverflow.com/questions/54252943/is-there-a-way-to-integrate-django-with-next-js#comment110078700_54252943

## License

MIT
