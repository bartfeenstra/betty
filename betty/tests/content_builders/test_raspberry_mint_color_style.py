from betty.content_builder import ContentBuilderManufacturer
from betty.content_builders.raspberry_mint_color_style import (
    ColorStyle,
    ColorStyleData,
)
from betty.content_builders.render import Render, RenderData
from betty.content_builders.static import Static
from betty.document import Document
from betty.extensions.raspberry_mint import ColorStyle as ColorStyleOption
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.data import DataTestBase


class TestColorStyleData(DataTestBase[ColorStyleData]):
    sut_cls = ColorStyleData

    def test_content(self) -> None:
        sut = ColorStyleData(
            ContentBuilderManufacturer("my-first-content"), style=ColorStyleOption.DARK
        )
        assert sut.content[0].plugin_id == "my-first-content"

    def test_style(self) -> None:
        style = ColorStyleOption.DARK_SECONDARY
        sut = ColorStyleData(
            ContentBuilderManufacturer("my-first-content"), style=style
        )
        assert sut.style == style


class TestColorStyle:
    async def test_build_template__without_content(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[ColorStyle]) as project:
            sut = await ColorStyle.new(
                project,
                ColorStyleData(
                    ContentBuilderManufacturer(Static),
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
                ColorStyleData(
                    ContentBuilderManufacturer(Render, RenderData("My First Content")),
                    style=ColorStyleOption.DARK,
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "My First Content" in actual
