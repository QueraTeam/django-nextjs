from django_nextjs.render import _get_context


def test_get_context():
    assert _get_context("") == None
    assert _get_context("<html></html>") == None
    assert _get_context("<html><head></head><body></body></html>") == None
    assert (
        _get_context(
            """<html><head></head><body><div id="__django_nextjs_body_begin"/><div id="__django_nextjs_body_end"/></body></html>"""
        )
        == None
    )
    html = """<html><head><link/></head><body id="__django_nextjs_body"><div id="__django_nextjs_body_begin"/><div id="__django_nextjs_body_end"/></body></html>"""
    expected_context = {
        "django_nextjs__": {
            "section1": "<html><head>",
            "section2": "<link/>",
            "section3": '</head><body id="__django_nextjs_body">',
            "section4": '<div id="__django_nextjs_body_begin"/>',
            "section5": '<div id="__django_nextjs_body_end"/></body></html>',
        }
    }
    assert _get_context(html) == expected_context

    context = {"extra_context": "content"}
    assert _get_context(html, context) == {**expected_context, **context}
