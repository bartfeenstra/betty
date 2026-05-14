"""
The box content plugin.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty.attrs.attr import AttrAttr
from betty.attrs.optional import Optional
from betty.attrs.plugin_manufacturer_sequence import (
    PluginManufacturerSequenceAttr,
)
from betty.content import Content, ContentDefinition, ContentManufacturer, build
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.str import StrDefinition
from betty.factory import DataManufacturable
from betty.locale.localizable.gettext import _
from betty.plugins.content.render import Render, RenderData
from betty.plugins.content.template import Template, TemplateBuild
from betty.project import Project
from betty.sample import Sample, Size

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.document import Document
    from betty.jinja import Environment
    from betty.plugin.factory import ResolvablePluginManufacturerSequence


@final
@ObjectDefinition(
    label=_("Box configuration"),
    samples=[
        lambda: Sample(BoxData([]), label="Minimal", size=Size.MINIMAL),
        lambda: Sample(
            BoxData(
                [ContentManufacturer(Render, RenderData("Hello, world!"))],
                min_height="100px",
                max_height="1000px",
                height="500px",
                min_width="100px",
                max_width="1000px",
                width="500px",
            ),
            label="Full",
            size=Size.FULL,
        ),
    ],
)
class BoxData(Data):
    """
    Configuration for :py:class:`betty.plugins.content.box.Box`.

    .. data:: betty.plugins.content.box:BoxData
    """

    content = PluginManufacturerSequenceAttr[ContentDefinition, Content](
        ContentManufacturer, label=_("Content")
    )
    """
    The content within this box.
    """

    min_height = Optional(AttrAttr(StrDefinition(label=_("Minimum height"))))
    max_height = Optional(AttrAttr(StrDefinition(label=_("Maximum height"))))
    height = Optional(AttrAttr(StrDefinition(label=_("Height"))))
    min_width = Optional(AttrAttr(StrDefinition(label=_("Minimum width"))))
    max_width = Optional(AttrAttr(StrDefinition(label=_("Maximum width"))))
    width = Optional(AttrAttr(StrDefinition(label=_("Width"))))

    def __init__(
        self,
        content: ResolvablePluginManufacturerSequence[ContentDefinition, Content],
        *,
        min_height: str | None = None,
        max_height: str | None = None,
        height: str | None = None,
        min_width: str | None = None,
        max_width: str | None = None,
        width: str | None = None,
    ):
        super().__init__()
        self.content = content
        self.min_height = min_height
        self.max_height = max_height
        self.height = height
        self.min_width = min_width
        self.max_width = max_width
        self.width = width


@final
@ContentDefinition("box", label=_("Box"))
class Box(Template, DataManufacturable[BoxData]):
    """
    .. plugin:: content:box.
    """

    def __init__(
        self,
        /,
        content: Iterable[Content],
        *,
        jinja: Environment,
        min_height: str | None = None,
        max_height: str | None = None,
        height: str | None = None,
        min_width: str | None = None,
        max_width: str | None = None,
        width: str | None = None,
    ):
        super().__init__(jinja=jinja)
        self._content = tuple(content)
        self._min_height = min_height
        self._max_height = max_height
        self._height = height
        self._min_width = min_width
        self._max_width = max_width
        self._width = width

    @override
    @classmethod
    def new_data_cls(cls) -> type[BoxData]:
        return BoxData

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, data: BoxData, /) -> Self:
        content, jinja = await gather(
            gather(
                *map(
                    project.factory.new,
                    map(ContentManufacturer.resolve, data.content),
                )
            ),
            project.jinja,
        )
        return cls(
            content=content,
            min_height=data.min_height,
            max_height=data.max_height,
            height=data.height,
            min_width=data.min_width,
            max_width=data.max_width,
            width=data.width,
            jinja=jinja,
        )

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        content = await build(document, self._content)
        if content is None:
            return None
        return "component/box.html.j2", {
            "box_content": content,
            "box_min_height": self._min_height,
            "box_max_height": self._max_height,
            "box_height": self._height,
            "box_min_width": self._min_width,
            "box_max_width": self._max_width,
            "box_width": self._width,
        }
