from typing import Optional

from .render import render_nextjs_page, stream_nextjs_page


def nextjs_page(
    *,
    stream: bool = False,
    template_name: str = "",
    context: Optional[dict] = None,
    using: Optional[str] = None,
    allow_redirects: bool = False,
    headers: Optional[dict] = None,
):
    if stream and (template_name or context or using):
        raise ValueError("When 'stream' is set to True, you should not use 'template_name', 'context', or 'using'")

    async def view(request, *args, **kwargs):
        if stream:
            return await stream_nextjs_page(request=request, allow_redirects=allow_redirects, headers=headers)

        return await render_nextjs_page(
            request=request,
            template_name=template_name,
            context=context,
            using=using,
            allow_redirects=allow_redirects,
            headers=headers,
        )

    return view
