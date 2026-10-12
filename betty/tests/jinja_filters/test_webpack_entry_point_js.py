from betty.project import Project
from betty.service_providers.webpack import Webpack
from betty.test_utils.conftest import AssertJinja


class TestWebpackEntryPointJs:
    async def test___call__(self, assert_jinja_str: AssertJinja) -> None:
        template = "{% do 'my-first-entry-point' | webpack_entry_point_js %}{{ document.webpack_js_entry_points | safe }}"
        Project.service_providers.add_init_plugins(assert_jinja_str.project, Webpack)
        async with assert_jinja_str(template) as rendered:
            assert rendered == "{'my-first-entry-point'}"
