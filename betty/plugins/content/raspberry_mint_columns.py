"""
The columns content plugin.
"""

from __future__ import annotations

from asyncio import gather
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, ClassVar, Self, final, override

from betty.assertion import (
    assert_enum,
    assert_int,
    assert_mapping,
    assert_or,
    assert_sequence,
)
from betty.attrs.attr import AttrAttr
from betty.attrs.optional import Optional
from betty.content import Content, ContentDefinition, ContentManufacturer, build
from betty.data import Data
from betty.datas.aggregate.collection.mapping import MappingDefinition
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.enum import EnumDefinition
from betty.datas.int import IntDefinition
from betty.datas.plugin_manufacturer_sequence import (
    PluginManufacturerSequenceDefinition,
)
from betty.factory import DataManufacturable
from betty.locale.localizable.gettext import _
from betty.plugins.asset_directory.raspberry_mint import RASPBERRY_MINT
from betty.plugins.content.render import Render, RenderData
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.extension.raspberry_mint import Breakpoint, JustifyContent
from betty.portable import CallbackPorter
from betty.project import Project
from betty.property import HasProperties
from betty.sample import Sample, Size

if TYPE_CHECKING:
    from betty.document import Document
    from betty.jinja import Environment
    from betty.plugin.factory import ResolvablePluginManufacturerSequence

type ColumnsWidth = Mapping[Breakpoint, Sequence[int]]
type ShorthandColumnsWidth = (
    int | Sequence[int] | Mapping[Breakpoint, int] | ColumnsWidth
)


@final
@ObjectDefinition(
    label=_("Columns configuration"),
    samples=[
        lambda: Sample(
            ColumnsData([ContentManufacturer(Render, RenderData("Hello, world!"))]),
            label="Minimal",
            size=Size.MINIMAL,
        ),
        lambda: Sample(
            ColumnsData(
                [ContentManufacturer(Render, RenderData("Hello, world!"))],
                justify_content=JustifyContent.CENTER,
            ),
            label="Justify content",
        ),
        lambda: Sample(
            ColumnsData(
                [ContentManufacturer(Render, RenderData("Hello, world!"))],
                width=6,
            ),
            label="A single column with a fixed, non-responsive width",
        ),
        lambda: Sample(
            ColumnsData(
                [
                    [
                        ContentManufacturer(Render, RenderData("Hello, world!")),
                    ],
                    [
                        ContentManufacturer(Render, RenderData("How are you?")),
                    ],
                ],
                width=[6, 6],
            ),
            label="Multiple columns with fixed, non-responsive widths",
        ),
        lambda: Sample(
            ColumnsData(
                [ContentManufacturer(Render, RenderData("Hello, world!"))],
                width={
                    Breakpoint.XS: 12,
                    Breakpoint.MD: 6,
                },
            ),
            label="A single column with responsive widths",
        ),
        lambda: Sample(
            ColumnsData(
                [
                    [
                        ContentManufacturer(Render, RenderData("Hello, world!")),
                    ],
                    [
                        ContentManufacturer(Render, RenderData("How are you?")),
                    ],
                ],
                width={
                    Breakpoint.XS: [12, 12],
                    Breakpoint.MD: [6, 6],
                },
            ),
            label="Multiple columns with responsive widths",
        ),
    ],
)
class ColumnsData(Data, HasProperties):
    """
    Configuration for :py:class:`betty.plugins.content.raspberry_mint_columns.Columns`.

    .. data:: betty.plugins.content.raspberry_mint_columns:ColumnsData
    """

    _DEFAULT_WIDTH: ClassVar[ColumnsWidth] = {Breakpoint.XS: [12]}
    _width: ColumnsWidth

    content = AttrAttr(
        SequenceDefinition(
            cls=list,
            value=PluginManufacturerSequenceDefinition(
                ContentManufacturer, label=_("Column content")
            ),
            label=_("Columns"),
        )
    )
    """
    The content within the columns.
    """

    justify_content = Optional(
        AttrAttr(EnumDefinition(cls=JustifyContent, label=_("Justify content")))
    )
    """
    If and how to justify content.
    """

    width = AttrAttr(
        MappingDefinition(
            cls=dict,
            key=EnumDefinition(
                cls=Breakpoint,
                label=_("Breakpoint"),
            ),
            value=SequenceDefinition(
                cls=list,
                label=_("Column widths"),
                value=IntDefinition(label=_("Column width")),
            ),
            label=_("Breakpoints"),
            porter=CallbackPorter(
                assert_or(
                    assert_or(
                        assert_int(),
                        assert_sequence(assert_int()),
                    ),
                    assert_or(
                        assert_mapping(assert_int(), assert_enum(Breakpoint)),
                        assert_mapping(
                            assert_sequence(assert_int()), assert_enum(Breakpoint)
                        ),
                    ),
                ),
                lambda data: {
                    breakpoint.value: widths
                    for breakpoint, widths in data.items()  # noqa: A001
                },
            ),
        )
    )
    """
    The column widths.
    """

    def __init__(
        self,
        /,
        content: Sequence[
            ResolvablePluginManufacturerSequence[ContentDefinition, Content]
        ],
        *,
        width: ShorthandColumnsWidth | None = None,
        justify_content: JustifyContent | None = None,
    ):
        super().__init__()
        self.content = list(map(ContentManufacturer.resolve_sequence, content))
        if width is None:
            self.width = self._DEFAULT_WIDTH
        elif isinstance(width, int):
            self.width = {Breakpoint.XS: [width]}
        elif isinstance(width, Mapping):
            self.width = {
                breakpoint: [columns] if isinstance(columns, int) else columns
                for breakpoint, columns in width.items()  # noqa: A001
            }
        else:
            self.width = {Breakpoint.XS: width}
        self.justify_content = justify_content


@final
@ContentDefinition(
    "raspberry-mint-columns",
    label=_("Columns"),
    requires={Project.asset_directories.require(RASPBERRY_MINT)},
)
class Columns(Template, DataManufacturable[ColumnsData]):
    """
    A container with one or more columns.

    .. plugin:: content:raspberry-mint-columns
    """

    def __init__(
        self,
        /,
        content: Iterable[Iterable[Content]],
        *,
        width: ColumnsWidth,
        jinja: Environment,
        justify_content: JustifyContent | None = None,
    ):
        super().__init__(jinja=jinja)
        self._content = tuple(map(tuple, content))
        self._justify_content = justify_content
        self._width = width

    @override
    @classmethod
    def new_data_cls(cls) -> type[ColumnsData]:
        return ColumnsData

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, data: ColumnsData, /) -> Self:
        content, jinja = await gather(
            gather(*[
                gather(
                    *map(
                        project.factory.new,
                        map(ContentManufacturer.resolve, column_content),
                    )
                )
                for column_content in data.content
            ]),
            project.jinja,
        )
        return cls(
            content=content,
            jinja=jinja,
            justify_content=data.justify_content,
            width=data.width,
        )

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        content = [
            await build(document, column_content) for column_content in self._content
        ]
        if not any(content):
            return None
        return "component/raspberry-mint/columns.html.j2", {
            "columns_content": content,
            "columns_justify_content": self._justify_content,
            "columns_width": {
                breakpoint.value: widths
                for breakpoint, widths in self._width.items()  # noqa: A001
            },
        }
