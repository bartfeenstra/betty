"""
The columns content plugin.
"""

from __future__ import annotations

from asyncio import gather
from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, ClassVar, Self, final, override

from betty.assertions.enum import assert_enum
from betty.assertions.if_else import assert_if_else
from betty.assertions.int import assert_int
from betty.assertions.mapping import assert_mapping
from betty.assertions.sequence import assert_sequence
from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.attrs.owner import OwnerAttr
from betty.classtools import TypeABCMeta
from betty.content_builder import (
    ContentBuilder,
    ContentBuilderDefinition,
    ContentBuilderManufacturer,
    ResolvableContentBuilderManufacturer,
    build,
)
from betty.content_builders.render import Render, RenderData
from betty.content_builders.template import Template, TemplateBuild
from betty.datas.aggregate.collection.dict import DictDefinition
from betty.datas.aggregate.collection.list import ListDefinition
from betty.datas.aggregate.record.object import Object, ObjectDefinition
from betty.datas.enum import EnumDefinition
from betty.datas.int import IntDefinition
from betty.datas.plugin.manufacturer.sequence import (
    PluginManufacturerSequenceDefinition,
)
from betty.factory import DataManufacturable
from betty.frosties.attr import AttrFreezable
from betty.localizables.gettext import _
from betty.porters.callback import CallbackPorter
from betty.project import Project
from betty.prop import HasProps
from betty.sample import Sample, Samples, Size
from betty.service_providers.raspberry_mint import Breakpoint, JustifyContent
from betty.typing import FrozenDict

if TYPE_CHECKING:
    from betty.document import Document
    from betty.jinja import Environment

type ColumnsWidth = Mapping[Breakpoint, Sequence[int]]
type ResolvableColumnsWidth = (
    int | Sequence[int] | Mapping[Breakpoint, int] | ColumnsWidth
)


def _resolve_columns_width(width: ResolvableColumnsWidth) -> ColumnsWidth:
    if isinstance(width, int):
        return FrozenDict({Breakpoint.XS: [width]})
    if isinstance(width, Mapping):
        return FrozenDict({
            breakpoint: (columns,) if isinstance(columns, int) else tuple(columns)
            for breakpoint, columns in width.items()  # noqa: A001
        })
    return FrozenDict({Breakpoint.XS: tuple(width)})


class _Columns:
    _DEFAULT_WIDTH: ClassVar[ColumnsWidth] = FrozenDict({Breakpoint.XS: [12]})

    _load_width = assert_int() | (lambda value: [value])
    _load_widths = assert_sequence(assert_int()) | list
    width = (
        OwnerAttr(
            DictDefinition(
                key=EnumDefinition(Breakpoint, label=_("Breakpoint")),
                value=ListDefinition(
                    label=_("Column widths"),
                    value=IntDefinition(label=_("Column width")),
                ),
                label=_("Breakpoints"),
                porter=CallbackPorter(
                    assert_if_else(
                        assert_if_else(_load_width, _load_widths)
                        | (lambda value: {Breakpoint.XS: value}),
                        assert_mapping(
                            assert_if_else(_load_width, _load_widths),
                            assert_enum(Breakpoint),
                        )
                        | dict,
                    ),
                    lambda data: {
                        breakpoint.value: widths
                        for breakpoint, widths in data.items()  # noqa: A001
                    },
                ),
            )
        )
        .setter(_resolve_columns_width)
        .default(lambda: _Columns._DEFAULT_WIDTH)
    )
    """
    The column widths.
    """

    justify_content = OwnerAttr(
        EnumDefinition(JustifyContent, label=_("Justify content"))
    ).optional
    """
    If and how to justify content.
    """


@final
@ObjectDefinition(
    label=_("Columns configuration"),
    samples=Samples(
        lambda: Sample(
            ColumnsData([
                ContentBuilderManufacturer(Render, RenderData("Hello, world!"))
            ]),
            label="Minimal",
            size=Size.MINIMAL,
        ),
        lambda: Sample(
            ColumnsData(
                [ContentBuilderManufacturer(Render, RenderData("Hello, world!"))],
                justify_content=JustifyContent.CENTER,
            ),
            label="Justify content",
        ),
        lambda: Sample(
            ColumnsData(
                [ContentBuilderManufacturer(Render, RenderData("Hello, world!"))],
                width=6,
            ),
            label="A single column with a fixed, non-responsive width",
        ),
        lambda: Sample(
            ColumnsData(
                [
                    ContentBuilderManufacturer(Render, RenderData("Hello, world!")),
                ],
                [
                    ContentBuilderManufacturer(Render, RenderData("How are you?")),
                ],
                width=[6, 6],
            ),
            label="Multiple columns with fixed, non-responsive widths",
        ),
        lambda: Sample(
            ColumnsData(
                [ContentBuilderManufacturer(Render, RenderData("Hello, world!"))],
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
                    ContentBuilderManufacturer(Render, RenderData("Hello, world!")),
                ],
                [
                    ContentBuilderManufacturer(Render, RenderData("How are you?")),
                ],
                width={
                    Breakpoint.XS: [12, 12],
                    Breakpoint.MD: [6, 6],
                },
            ),
            label="Multiple columns with responsive widths",
        ),
    ),
    manufacturer=lambda **fields: ColumnsData(*fields.pop("content"), **fields),
)
class ColumnsData(_Columns, Object, AttrFreezable):
    """
    Configuration for :py:class:`betty.content_builders.raspberry_mint_columns.Columns`.

    .. data:: betty.content_builders.raspberry_mint_columns:ColumnsData
    """

    content = OwnerAttr(
        ListDefinition(
            value=PluginManufacturerSequenceDefinition(
                ContentBuilderManufacturer, label=_("Column content")
            ),
            label=_("Columns"),
        )
    )
    """
    The content within the columns.
    """

    def __init__(
        self,
        *content: Iterable[ResolvableContentBuilderManufacturer],
        width: ResolvableColumnsWidth = _Columns._DEFAULT_WIDTH,
        justify_content: JustifyContent | None = None,
    ):
        super().__init__()
        self.content = tuple(
            tuple(map(ContentBuilderManufacturer.resolve, column_content))
            for column_content in content
        )
        self.width = width
        self.justify_content = justify_content


@final
@ContentBuilderDefinition(
    "raspberry-mint-columns",
    label=_("Columns"),
    requires={Project.asset_directories.require(raspberry_mint)},
)
class Columns(
    Template, DataManufacturable[ColumnsData], HasProps, metaclass=TypeABCMeta
):
    """
    A container with one or more columns.

    .. plugin:: content-builder:raspberry-mint-columns
    """

    def __init__(
        self,
        /,
        *content: Iterable[ContentBuilder],
        width: ColumnsWidth = _Columns._DEFAULT_WIDTH,
        jinja: Environment,
        justify_content: JustifyContent | None = None,
    ):
        super().__init__(jinja=jinja)
        self._content = tuple(map(tuple, content))
        self.justify_content = justify_content
        self.width = width

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
                        map(ContentBuilderManufacturer.resolve, column_content),
                    )
                )
                for column_content in data.content
            ]),
            project.jinja,
        )
        return cls(
            *content,
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
            "columns_justify_content": self.justify_content,
            "columns_width": {
                breakpoint.value: widths
                for breakpoint, widths in self.width.items()  # noqa: A001
            },
        }
