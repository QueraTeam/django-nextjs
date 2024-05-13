from typing import Dict, Union

from .render import render_nextjs_page


def nextjs_page(
    *,
    template_name: str = "",
    context: Union[Dict, None] = None,
    using: Union[str, None] = None,
    allow_redirects: bool = False,
    headers: Union[Dict, None] = None,
):
    async def view(request, *args, **kwargs):
        return await render_nextjs_page(
            request=request,
            template_name=template_name,
            context=context,
            using=using,
            allow_redirects=allow_redirects,
            headers=headers,
        )

    return view
