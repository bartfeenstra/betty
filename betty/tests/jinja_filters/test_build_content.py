from collections.abc import Iterable

import pytest

from betty.content import Content, ContentDefinition
from betty.plugin.factory import PluginManufacturer
from betty.plugins.content.static import Static
from betty.test_utils.conftest import AssertTemplateString


class TestBuildContent:
    @pytest.mark.parametrize(
        ("expected", "contents"),
        [
            ("", []),
            (
                "Hello, world!",
                [Static("Hello, world!")],
            ),
        ],
    )
    async def test___call__(
        self,
        assert_template_string: AssertTemplateString,
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
