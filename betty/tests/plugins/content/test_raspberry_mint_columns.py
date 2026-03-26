import pytest

from betty.app import App
from betty.content import ContentManufacturer
from betty.document import Document
from betty.plugins.content.raspberry_mint_columns import (
    Columns,
    ColumnsConfiguration,
    ColumnsWidth,
    ShorthandColumnsWidth,
)
from betty.plugins.content.render import Render, RenderConfiguration
from betty.plugins.extension.raspberry_mint import (
    Breakpoint,
    JustifyContent,
)
from betty.project import Project
from betty.test_utils.data import DataTestBase
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestColumnsConfiguration(DataTestBase[ColumnsConfiguration]):
    sut_cls = ColumnsConfiguration

    def test_content(self) -> None:
        content = ContentManufacturer(Render, RenderConfiguration(DUMMY_LOCALIZABLE))
        sut = ColumnsConfiguration([content])
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
            ColumnsConfiguration(
                [[ContentManufacturer(Render, RenderConfiguration(DUMMY_LOCALIZABLE))]],
                width=width,
            ).width
            == expected
        )

    def test_justify_content(self) -> None:
        justify_content = JustifyContent.CENTER
        sut = ColumnsConfiguration(
            [[ContentManufacturer(Render, RenderConfiguration(DUMMY_LOCALIZABLE))]],
            justify_content=justify_content,
        )
        assert sut.justify_content == justify_content


class TestColumns:
    async def test_build_template__minimal(self, isolated_app: App) -> None:
        async with (
            Project.new_isolated(isolated_app, support_plugins=[Columns]) as project,
            project,
        ):
            sut = await Columns.new(
                project,
                ColumnsConfiguration(
                    [
                        [
                            ContentManufacturer(
                                Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                            )
                        ]
                    ]
                ),
            )
            actual = await sut.build(document=Document())
        assert actual is not None
        assert "col col-12" in actual

    async def test_build_template__single_column_multiple_breakpoints(
        self, isolated_app: App
    ) -> None:
        async with (
            Project.new_isolated(isolated_app, support_plugins=[Columns]) as project,
            project,
        ):
            sut = await Columns.new(
                project,
                ColumnsConfiguration(
                    [
                        [
                            ContentManufacturer(
                                Render, RenderConfiguration(DUMMY_LOCALIZABLE)
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
        self, isolated_app: App
    ) -> None:
        async with (
            Project.new_isolated(isolated_app, support_plugins=[Columns]) as project,
            project,
        ):
            sut = await Columns.new(
                project,
                ColumnsConfiguration(
                    [
                        [
                            ContentManufacturer(
                                Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                            )
                        ],
                        [
                            ContentManufacturer(
                                Render, RenderConfiguration(DUMMY_LOCALIZABLE)
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
        self, isolated_app: App
    ) -> None:
        async with (
            Project.new_isolated(isolated_app, support_plugins=[Columns]) as project,
            project,
        ):
            sut = await Columns.new(
                project,
                ColumnsConfiguration(
                    [
                        [
                            ContentManufacturer(
                                Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                            )
                        ],
                        [
                            ContentManufacturer(
                                Render, RenderConfiguration(DUMMY_LOCALIZABLE)
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
