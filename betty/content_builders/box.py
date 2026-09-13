"""
The box content plugin.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty.attrs.new_plugin_sequence import (
    new_new_plugin_sequence_attr,
)
from betty.attrs.owner import OwnerAttr
from betty.content_builder import (
    ContentBuilder,
    ContentBuilderDefinition,
    NewContentBuilder,
    ResolvableContentBuilderManufacturer,
    build,
)
from betty.content_builders.render import Render, RenderConfig
from betty.content_builders.template import Template, TemplateBuild
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.str import StrDefinition
from betty.localizables.gettext import _
from betty.plugin.factory import ConfigurableIntegratable, new
from betty.project import Project
from betty.prop import HasProps
from betty.sample import Sample, Size

if TYPE_CHECKING:
    from betty.document import Document
    from betty.jinja import Environment


@final
@ObjectDefinition(
    label=_("Box configuration"),
    samples=[
        lambda: Sample(BoxConfig(), label="Minimal", size=Size.MINIMAL),
        lambda: Sample(
            BoxConfig(
                NewContentBuilder(Render, RenderConfig("Hello, world!")),
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
    manufacturer=lambda **fields: BoxConfig(*fields.pop("content"), **fields),
)
class BoxConfig(Data, HasProps):
    """
    Configuration for :py:class:`betty.content_builders.box.Box`.

    .. data:: betty.content_builders.box:BoxData
    """

    content = new_new_plugin_sequence_attr(NewContentBuilder, label=_("Content"))
    """
    The content within this box.
    """

    min_height = OwnerAttr(StrDefinition(label=_("Minimum height"))).optional
    max_height = OwnerAttr(StrDefinition(label=_("Maximum height"))).optional
    height = OwnerAttr(StrDefinition(label=_("Height"))).optional
    min_width = OwnerAttr(StrDefinition(label=_("Minimum width"))).optional
    max_width = OwnerAttr(StrDefinition(label=_("Maximum width"))).optional
    width = OwnerAttr(StrDefinition(label=_("Width"))).optional

    def __init__(
        self,
        *content: ResolvableContentBuilderManufacturer,
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
@ContentBuilderDefinition("box", label=_("Box"), config_cls=BoxConfig)
class Box(Template, ConfigurableIntegratable[BoxConfig]):
    """
    .. plugin:: content-builder:box.
    """

    def __init__(
        self,
        /,
        *content: ContentBuilder,
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
    @Project.require
    @classmethod
    async def new(cls, project: Project, config: BoxConfig, /) -> Self:
        content, jinja = await gather(
            gather(
                *map(
                    lambda manufacturer: new(manufacturer, project),
                    map(NewContentBuilder.resolve, config.content),
                )
            ),
            project.jinja,
        )
        return cls(
            *content,
            min_height=config.min_height,
            max_height=config.max_height,
            height=config.height,
            min_width=config.min_width,
            max_width=config.max_width,
            width=config.width,
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
