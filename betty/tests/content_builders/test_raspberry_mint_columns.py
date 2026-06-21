import pytest

from betty.content_builder import ContentBuilderManufacturer
from betty.content_builders.raspberry_mint_columns import (
    Columns,
    ColumnsData,
    ColumnsWidth,
    ShorthandColumnsWidth,
)
from betty.content_builders.render import Render, RenderData
from betty.document import Document
from betty.extensions.raspberry_mint import Breakpoint, JustifyContent
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.data import DataTestBase
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestColumnsData(DataTestBase[ColumnsData]):
    sut_cls = ColumnsData

    def test_content(self) -> None:
        content = ContentBuilderManufacturer(Render, RenderData(DUMMY_LOCALIZABLE))
        sut = ColumnsData([content])
        assert list(map(list, sut.content)) == [[content]]

    @pytest.mark.parametrize(
        ("expected", "width"),
        [
            ({Breakpoint.XS: [7]}, 7),
            ({Breakpoint.XS: [7]}, [7]),
            ({Breakpoint.XS: [7]}, {Breakpoint.XS: 7}),
            ({Breakpoint.XS: [7]}, {Breakpoint.XS: [7]}),
        ],
    )
    def test_width(self, expected: ColumnsWidth, width: ShorthandColumnsWidth) -> None:
        assert (
            ColumnsData(
                [[ContentBuilderManufacturer(Render, RenderData(DUMMY_LOCALIZABLE))]],
                width=width,
            ).width
            == expected
        )

    def test_justify_content(self) -> None:
        justify_content = JustifyContent.CENTER
        sut = ColumnsData(
            [[ContentBuilderManufacturer(Render, RenderData(DUMMY_LOCALIZABLE))]],
            justify_content=justify_content,
        )
        assert sut.justify_content == justify_content


class TestColumns:
    async def test_build_template__minimal(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[Columns]) as project:
            sut = await Columns.new(
                project,
                ColumnsData([
                    [ContentBuilderManufacturer(Render, RenderData(DUMMY_LOCALIZABLE))]
                ]),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "col col-12" in actual

    async def test_build_template__single_column_multiple_breakpoints(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[Columns]) as project:
            sut = await Columns.new(
                project,
                ColumnsData(
                    [
                        [
                            ContentBuilderManufacturer(
                                Render, RenderData(DUMMY_LOCALIZABLE)
                            )
                        ]
                    ],
                    width={Breakpoint.XS: 12, Breakpoint.LG: 6},
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "col col-12 col-lg-6" in actual

    async def test_build_template__multiple_columns_single_breakpoint(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[Columns]) as project:
            sut = await Columns.new(
                project,
                ColumnsData(
                    [
                        [
                            ContentBuilderManufacturer(
                                Render, RenderData(DUMMY_LOCALIZABLE)
                            )
                        ],
                        [
                            ContentBuilderManufacturer(
                                Render, RenderData(DUMMY_LOCALIZABLE)
                            )
                        ],
                    ],
                    width=[8, 4],
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "col col-8" in actual
        assert "col col-4" in actual

    async def test_build_template__multiple_columns_multiple_breakpoints(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[Columns]) as project:
            sut = await Columns.new(
                project,
                ColumnsData(
                    [
                        [
                            ContentBuilderManufacturer(
                                Render, RenderData(DUMMY_LOCALIZABLE)
                            )
                        ],
                        [
                            ContentBuilderManufacturer(
                                Render, RenderData(DUMMY_LOCALIZABLE)
                            )
                        ],
                    ],
                    width={Breakpoint.XS: [8, 4], Breakpoint.LG: [7, 5]},
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "col col-8 col-lg-7" in actual
        assert "col col-4 col-lg-5" in actual
