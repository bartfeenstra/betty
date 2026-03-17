from betty.plugins.extension.webpack import Webpack
from betty.test_utils.jinja import assert_template_string


class TestWebpackEntryPointJs:
    async def test___call__(self) -> None:
        template = "{% do 'my-first-entry-point' | webpack_entry_point_js %}{{ document.webpack_js_entry_points | safe }}"
        async with assert_template_string(template=template, extensions={Webpack}) as (
            actual,
            _,
        ):
            assert actual == "{'my-first-entry-point'}"
