from collections.abc import Iterable

import pytest

from betty.content import Content, ContentDefinition, ContentManufacturer
from betty.plugin.factory import PluginManufacturer
from betty.plugins.content.render import Render, RenderConfiguration
from betty.test_utils.jinja import assert_template_string


class TestBuildContent:
    @pytest.mark.parametrize(
        ("expected", "contents"),
        [
            ("", []),
            (
                "<p>Hello, world!</p>",
                [ContentManufacturer(Render, RenderConfiguration("Hello, world!"))],
            ),
        ],
    )
    async def test___call__(
        self,
        expected: str,
        contents: Iterable[PluginManufacturer[ContentDefinition, Content]],
    ) -> None:
        template = "{{ data | build_content }}"
        async with assert_template_string(
            template=template,
            data={
                "data": contents,
            },
        ) as (actual, _):
            assert actual == expected
