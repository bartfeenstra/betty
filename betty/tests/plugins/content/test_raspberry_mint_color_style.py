from betty.content import ContentManufacturer
from betty.document import Document
from betty.plugins.content.raspberry_mint_color_style import (
    ColorStyle,
    ColorStyleConfiguration,
)
from betty.plugins.content.render import Render, RenderConfiguration
from betty.plugins.content.static import Static
from betty.plugins.extension.raspberry_mint import ColorStyle as ColorStyleOption
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.data import DataTestBase


class TestColorStyleConfiguration(DataTestBase[ColorStyleConfiguration]):
    sut_cls = ColorStyleConfiguration

    def test_content(self) -> None:
        sut = ColorStyleConfiguration(
            ContentManufacturer("my-first-content"), style=ColorStyleOption.DARK
        )
        assert sut.content[0].plugin_id == "my-first-content"

    def test_style(self) -> None:
        style = ColorStyleOption.DARK_SECONDARY
        sut = ColorStyleConfiguration(
            ContentManufacturer("my-first-content"), style=style
        )
        assert sut.style == style


class TestColorStyle:
    async def test_build_template__without_content(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(support_plugins=[ColorStyle]) as project:
            sut = await ColorStyle.new(
                project,
                ColorStyleConfiguration(
                    ContentManufacturer(Static),
                    style=ColorStyleOption.DARK,
                ),
            )
            assert await sut.build(document=Document()) is None

    async def test_build_template__with_content(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(support_plugins=[ColorStyle]) as project:
            sut = await ColorStyle.new(
                project,
                ColorStyleConfiguration(
                    ContentManufacturer(
                        Render, RenderConfiguration("My First Content")
                    ),
                    style=ColorStyleOption.DARK,
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "My First Content" in actual
