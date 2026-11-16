import pytest

from betty.collections.mapping.dict import FrozenDict
from betty.content_builder import ContentBuilderManufacturer
from betty.content_builders.raspberry_mint_columns import (
    Columns,
    ColumnsConfig,
    ColumnsWidth,
    ResolvableColumnsWidth,
)
from betty.content_builders.render import Render, RenderConfig
from betty.document import Document
from betty.service_providers.raspberry_mint import Breakpoint, JustifyContent
from betty.test_utils.conftest import NewIsolatedProject
from betty.test_utils.data import DataTestBase


class TestColumnsConfig(DataTestBase[ColumnsConfig]):
    sut_cls = ColumnsConfig

    def test_content(self) -> None:
        content = ContentBuilderManufacturer(Render, RenderConfig("-"))
        sut = ColumnsConfig([content])
        assert list(map(list, sut.content)) == [[content]]

    @pytest.mark.parametrize(
        ("expected", "width"),
        [
            (FrozenDict({Breakpoint.XS: (7,)}), 7),
            (FrozenDict({Breakpoint.XS: (7,)}), (7,)),
            (FrozenDict({Breakpoint.XS: (7,)}), {Breakpoint.XS: 7}),
            (FrozenDict({Breakpoint.XS: (7,)}), {Breakpoint.XS: (7,)}),
        ],
    )
    def test_width(self, expected: ColumnsWidth, width: ResolvableColumnsWidth) -> None:
        assert (
            ColumnsConfig(
                [ContentBuilderManufacturer(Render, RenderConfig("-"))],
                width=width,
            ).width
            == expected
        )

    def test_justify_content(self) -> None:
        justify_content = JustifyContent.CENTER
        sut = ColumnsConfig(
            [ContentBuilderManufacturer(Render, RenderConfig("-"))],
            justify_content=justify_content,
        )
        assert sut.justify_content == justify_content


class TestColumns:
    async def test_build_template__minimal(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with (
            new_isolated_project(supported_plugins=[Columns]) as project,
            project,
        ):
            sut = await Columns.new(
                project,
                ColumnsConfig([ContentBuilderManufacturer(Render, RenderConfig("-"))]),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "col col-12" in actual

    async def test_build_template__single_column_multiple_breakpoints(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with (
            new_isolated_project(supported_plugins=[Columns]) as project,
            project,
        ):
            sut = await Columns.new(
                project,
                ColumnsConfig(
                    [ContentBuilderManufacturer(Render, RenderConfig("-"))],
                    width={Breakpoint.XS: 12, Breakpoint.LG: 6},
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "col col-12 col-lg-6" in actual

    async def test_build_template__multiple_columns_single_breakpoint(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with (
            new_isolated_project(supported_plugins=[Columns]) as project,
            project,
        ):
            sut = await Columns.new(
                project,
                ColumnsConfig(
                    [ContentBuilderManufacturer(Render, RenderConfig("-"))],
                    [ContentBuilderManufacturer(Render, RenderConfig("-"))],
                    width=[8, 4],
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "col col-8" in actual
        assert "col col-4" in actual

    async def test_build_template__multiple_columns_multiple_breakpoints(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with (
            new_isolated_project(supported_plugins=[Columns]) as project,
            project,
        ):
            sut = await Columns.new(
                project,
                ColumnsConfig(
                    [ContentBuilderManufacturer(Render, RenderConfig("-"))],
                    [ContentBuilderManufacturer(Render, RenderConfig("-"))],
                    width={Breakpoint.XS: [8, 4], Breakpoint.LG: [7, 5]},
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "col col-8 col-lg-7" in actual
        assert "col col-4 col-lg-5" in actual
