# Django Next.js

Next.js + Django integration

From a [comment on StackOverflow]:

> Run 2 ports on the same server. One for django (public facing)
> and one for Next.js (internal).
> Let django handle all web requests.
> For each request, query Next.js from django view to get HTML response.
> Return that exact HTML response from django view.

## Installation

1. Install the python package.
2. Add `nextjs` to `INSTALLED_APPS`. It must be before `django_js_reverse`.
3. Add the following to the beginning of `urls.py`:

   ```python
   path("", include("nextjs.urls"))
   ```

## Usage

Start Next.js server:

```shell
$ npm run dev
```

Develop your pages in Next.js.
Write a django URL and view for each page like this:

```python
from nextjs.render import render_nextjs_page

def jobs(request):
    return render_nextjs_page(request)
```

## Notes

If you want to add a file to `public` directory of Next.js,
that file should be in `public/next` subdirectory to work correctly.


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
