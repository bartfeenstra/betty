"""
The color style content plugin.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import RASPBERRY_MINT
from betty.attrs.attr import AttrAttr
from betty.attrs.plugin_manufacturer_sequence import (
    new_plugin_manufacturer_sequence_attr,
)
from betty.content import (
    ContentBuilder,
    ContentBuilderDefinition,
    ContentBuilderManufacturer,
    build,
)
from betty.content_builders.template import Template, TemplateBuild
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.enum import EnumDefinition
from betty.extensions.raspberry_mint import ColorStyle as RaspberryMintColorStyle
from betty.factory import DataManufacturable
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.prop import HasProps
from betty.sample import Sample

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.document import Document
    from betty.jinja import Environment
    from betty.plugin.factory import ResolvablePluginManufacturerSequence


@final
@ObjectDefinition(
    label=_("Color style configuration"),
    samples=[
        lambda: Sample(
            ColorStyleData("my-first-content", style=RaspberryMintColorStyle.DARK),
            label="Default",
        )
    ],
)
class ColorStyleData(Data, HasProps):
    """
    Configuration for :py:class:`betty.content_builders.raspberry_mint_color_style.ColorStyle`.

    .. data:: betty.content_builders.raspberry_mint_color_style:ColorStyleData
    """

    content = new_plugin_manufacturer_sequence_attr(
        ContentBuilderManufacturer, label=_("Content")
    )
    """
    The content within this color style.
    """

    style = AttrAttr(EnumDefinition(cls=RaspberryMintColorStyle, label=_("Style")))
    """
    The style.
    """

    def __init__(
        self,
        content: ResolvablePluginManufacturerSequence[
            ContentBuilderDefinition, ContentBuilder
        ],
        *,
        style: RaspberryMintColorStyle,
    ):
        super().__init__()
        self.style = style
        self.content = content


@final
@ContentBuilderDefinition(
    "raspberry-mint-color-style",
    label=_("Color style"),
    requires={Project.asset_directories.require(RASPBERRY_MINT)},
)
class ColorStyle(Template, DataManufacturable[ColorStyleData]):
    """
    Change the color style for all containing content.

    .. plugin:: content-builder:raspberry-mint-color-style
    """

    def __init__(
        self,
        /,
        content: Iterable[ContentBuilder],
        *,
        jinja: Environment,
        style: RaspberryMintColorStyle,
    ):
        super().__init__(jinja=jinja)
        self._content = tuple(content)
        self._style = style

    @override
    @classmethod
    def new_data_cls(cls) -> type[ColorStyleData]:
        return ColorStyleData

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, data: ColorStyleData, /) -> Self:
        content, jinja = await gather(
            gather(
                *map(
                    project.factory.new,
                    data.content,
                )
            ),
            project.jinja,
        )
        return cls(content=content, jinja=jinja, style=data.style)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        content = await build(document, self._content)
        if content is None:
            return None
        return "component/raspberry-mint/color-style.html.j2", {
            "color_style": self._style.value,
            "color_style_content": content,
        }
