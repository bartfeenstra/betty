from betty.content_builder import ContentBuilderManufacturer
from betty.content_builders.raspberry_mint_color_style import (
    ColorStyle,
    ColorStyleConfig,
)
from betty.content_builders.render import Render, RenderConfig
from betty.content_builders.static import Static
from betty.document import Document
from betty.service_providers.raspberry_mint import ColorStyle as ColorStyleOption
from betty.test_utils.conftest import NewIsolatedProject
from betty.test_utils.data import DataTestBase


class TestColorStyleConfig(DataTestBase[ColorStyleConfig]):
    sut_cls = ColorStyleConfig

    def test_content(self) -> None:
        sut = ColorStyleConfig(
            ContentBuilderManufacturer("my-first-content"), style=ColorStyleOption.DARK
        )
        assert sut.content[0].plugin_id == "my-first-content"

    def test_style(self) -> None:
        style = ColorStyleOption.DARK_SECONDARY
        sut = ColorStyleConfig(
            ContentBuilderManufacturer("my-first-content"), style=style
        )
        assert sut.style == style


class TestColorStyle:
    async def test_build_template__without_content(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with (
            new_isolated_project(support=[ColorStyle]) as project,
            project,
        ):
            sut = await ColorStyle.new(
                project,
                ColorStyleConfig(
                    ContentBuilderManufacturer(Static),
                    style=ColorStyleOption.DARK,
                ),
            )
            assert await sut.build(document=Document()) is None

    async def test_build_template__with_content(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with (
            new_isolated_project(support=[ColorStyle]) as project,
            project,
        ):
            sut = await ColorStyle.new(
                project,
                ColorStyleConfig(
                    ContentBuilderManufacturer(
                        Render, RenderConfig("My First Content")
                    ),
                    style=ColorStyleOption.DARK,
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "My First Content" in actual
