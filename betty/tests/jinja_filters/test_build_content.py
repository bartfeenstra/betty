from collections.abc import Iterable

import pytest

from betty.content_builder import ContentBuilder, ContentBuilderDefinition
from betty.content_builders.static import Static
from betty.plugin.factory import PluginManufacturer
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
        contents: Iterable[
            PluginManufacturer[ContentBuilderDefinition, ContentBuilder]
        ],
    ) -> None:
        template = "{{ data | build_content }}"
        async with assert_template_string(
            template=template,
            data={
                "data": contents,
            },
        ) as (actual, _):
            assert actual == expected
