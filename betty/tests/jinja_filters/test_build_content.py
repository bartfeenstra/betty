from collections.abc import Iterable

import pytest

from betty.content_builder import ContentBuilder, ContentBuilderDefinition
from betty.content_builders.static import Static
from betty.plugin.factory import PluginManufacturer
from betty.test_utils.conftest import AssertJinja


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
        assert_jinja_str: AssertJinja,
        expected: str,
        contents: Iterable[
            PluginManufacturer[ContentBuilderDefinition, ContentBuilder]
        ],
    ) -> None:
        template = "{{ data | build_content }}"
        async with assert_jinja_str(template, data={"data": contents}) as rendered:
            assert rendered == expected
