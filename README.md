# Django Next.js

Next.js + Django integration

From a [comment on StackOverflow]:

> Run 2 ports on the same server. One for django (public facing)
> and one for Next.js (internal).
> Let django handle all web requests.
> For each request, query Next.js from django view to get HTML response.
> Return that exact HTML response from django view.

## Installation

- Install the python package.
- Add `nextjs` to `INSTALLED_APPS`. It must be before `django_js_reverse`.

- **In Development Environment:**

  - If you're using django channels, add `NextJSProxyConsumer` to `asgi.py`:

    ```python
    import os
    
    from django.core.asgi import get_asgi_application
    from django.urls import re_path
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
    django_asgi_app = get_asgi_application()
    
    from channels.routing import ProtocolTypeRouter, URLRouter
    from nextjs.proxy import NextJSProxyConsumer
    
    from django.conf import settings
    
    http_routes = [re_path(r"", django_asgi_app)]
    if settings.DEBUG:
        http_routes.insert(0, re_path(r"^(?:_next|__next|next).*", NextJSProxyConsumer.as_asgi()))
    
    application = ProtocolTypeRouter(
        {
            # Django's ASGI application to handle traditional HTTP requests
            "http": URLRouter(http_routes),
            # ...
        }
    )
    ```

  - Otherwise, add the following to the beginning of `urls.py`:

    ```python
    path("", include("nextjs.urls"))
    ```

- **In Production:**

  - Use a reverse proxy like nginx:

    | URL | Action |
    |-----|--------|
    | `/_next/static/...` | Serve `NEXTJS_PATH/.next/static` directory | 
    | `/_next/...` | Proxy to  `http://localhost:3000` |
    | `/next/...` | Serve `NEXTJS_PATH/public/next` directory |

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
from nextjs.render import render_nextjs_page_async

async def jobs(request):
    return await render_nextjs_page_async(request)
```

```python
# If you're not using django channels
from nextjs.render import render_nextjs_page_sync

def jobs(request):
    return render_nextjs_page_sync(request)
```

## Notes

- If you want to add a file to `public` directory of Next.js,
  that file should be in `public/next` subdirectory to work correctly.
- If you're using django channels, make sure all your middlewares are
  [async-capable](https://docs.djangoproject.com/en/3.1/topics/http/middleware/#asynchronous-support).


## Settings

Default settings:

    NEXTJS_SETTINGS = {
        "nextjs_server_url": "http://127.0.0.1:3000",
        "nextjs_reverse_path": os.path.join(settings.BASE_DIR, "next", "reverse"),
    }

### `nextjs_server_url`

The URL of Next.js server (started by `npm run dev` or `npm run start`)

### `nextjs_reverse_path`

Path to a directory where generated `reverse.json` file is saved.


## References

- https://github.com/yourlabs/djnext
- [comment on StackOverflow]

[comment on StackOverflow]: https://stackoverflow.com/questions/54252943/is-there-a-way-to-integrate-django-with-next-js#comment110078700_54252943
