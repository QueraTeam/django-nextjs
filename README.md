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

2. You need both Django templates and Next.js at the same time and those pages should easily link to eachother.
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

## Customizing Document

If you want to customize the HTML document (e.g. add header or footer), read this section.

You need to [customize Next's document]:

- Add `id="__django_nextjs_body"` as the first attribute of `<body>` element.
- Add `<div id="__django_nextjs_body_begin" />` as the first element inside `<body>`.
- Add `<div id="__django_nextjs_body_end" />` as the last element inside `<body>`.

```jsx
import Document, { Html, Head, Main, NextScript } from "next/document";

// https://nextjs.org/docs/advanced-features/custom-document
class MyDocument extends Document {
  render() {
    return (
      <Html>
        <Head />
        <body id="__django_nextjs_body" dir="rtl">
          <div id="__django_nextjs_body_begin" />
          <Main />
          <NextScript />
          <div id="__django_nextjs_body_end" />
        </body>
      </Html>
    );
  }
}

export default MyDocument;
```

Write a django template that extends `django_nextjs/document_base.html`:

```django
{% extends "django_nextjs/document_base.html" %}


{% block head %}
  ... the content you want to add to the beginning of <head> tag ...
  {{ block.super }}
  ... the content you want to add to the end of <head> tag ...
{% endblock %}


{% block body %}
  ... the content you want to add to the beginning of <body> tag ...
  {{ block.super }}
  ... the content you want to add to the end of <body> tag ...
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
[customize next's document]: https://nextjs.org/docs/advanced-features/custom-document

## License

MIT
