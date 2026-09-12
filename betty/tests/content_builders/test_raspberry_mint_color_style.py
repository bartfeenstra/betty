from betty.content_builder import NewContentBuilder
from betty.content_builders.raspberry_mint_color_style import (
    ColorStyle,
    ColorStyleConfig,
)
from betty.content_builders.render import Render, RenderConfig
from betty.content_builders.static import Static
from betty.document import Document
from betty.service_providers.raspberry_mint import ColorStyle as ColorStyleOption
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.data import DataTestBase


class TestColorStyleData(DataTestBase[ColorStyleConfig]):
    sut_cls = ColorStyleConfig

    def test_content(self) -> None:
        sut = ColorStyleConfig(
            NewContentBuilder("my-first-content"), style=ColorStyleOption.DARK
        )
        assert sut.content[0].id == "my-first-content"

    def test_style(self) -> None:
        style = ColorStyleOption.DARK_SECONDARY
        sut = ColorStyleConfig(NewContentBuilder("my-first-content"), style=style)
        assert sut.style == style


class TestColorStyle:
    async def test_build_template__without_content(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[ColorStyle]) as project:
            sut = await ColorStyle.new(
                project,
                ColorStyleConfig(
                    NewContentBuilder(Static),
                    style=ColorStyleOption.DARK,
                ),
            )
            assert await sut.build(document=Document()) is None

    async def test_build_template__with_content(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[ColorStyle]) as project:
            sut = await ColorStyle.new(
                project,
                ColorStyleConfig(
                    NewContentBuilder(Render, RenderConfig("My First Content")),
                    style=ColorStyleOption.DARK,
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "My First Content" in actual
