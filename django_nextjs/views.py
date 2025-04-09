from typing import Dict, Union

from .render import render_nextjs_page, stream_nextjs_page


def nextjs_page(
    *,
    stream: bool = False,
    template_name: str = "",
    context: Union[Dict, None] = None,
    using: Union[str, None] = None,
    allow_redirects: bool = False,
    headers: Union[Dict, None] = None,
):
    if stream and (template_name or context or using):
        raise ValueError(
            "When 'stream' parameter is True, 'template_name', 'context', and 'using' cannot be used together."
        )

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
