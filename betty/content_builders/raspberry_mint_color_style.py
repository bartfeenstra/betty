"""
The color style content plugin.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import raspberry_mint
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
from betty.content_builders.template import Template, TemplateBuild
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.enum import EnumDefinition
from betty.localizables.gettext import _
from betty.plugin.factory import ConfigurableIntegratable, new
from betty.project import Project
from betty.prop import HasProps
from betty.sample import Sample
from betty.service_providers.raspberry_mint import ColorStyle as RaspberryMintColorStyle

if TYPE_CHECKING:
    from betty.document import Document
    from betty.jinja import Environment


@final
@ObjectDefinition(
    label=_("Color style configuration"),
    samples=[
        lambda: Sample(
            ColorStyleConfig("my-first-content", style=RaspberryMintColorStyle.DARK),
            label="Default",
        )
    ],
    manufacturer=lambda **fields: ColorStyleConfig(*fields.pop("content"), **fields),
)
class ColorStyleConfig(Data, HasProps):
    """
    Configuration for :py:class:`betty.content_builders.raspberry_mint_color_style.ColorStyle`.

    .. data:: betty.content_builders.raspberry_mint_color_style:ColorStyleData
    """

    content = new_new_plugin_sequence_attr(NewContentBuilder, label=_("Content"))
    """
    The content within this color style.
    """

    style = OwnerAttr(EnumDefinition(cls=RaspberryMintColorStyle, label=_("Style")))
    """
    The style.
    """

    def __init__(
        self,
        *content: ResolvableContentBuilderManufacturer,
        style: RaspberryMintColorStyle,
    ):
        super().__init__()
        self.style = style
        self.content = content


@final
@ContentBuilderDefinition(
    "raspberry-mint-color-style",
    label=_("Color style"),
    config_cls=ColorStyleConfig,
    requires={Project.asset_directories.require(raspberry_mint)},
)
class ColorStyle(Template, ConfigurableIntegratable[ColorStyleConfig]):
    """
    Change the color style for all containing content.

    .. plugin:: content-builder:raspberry-mint-color-style
    """

    def __init__(
        self,
        /,
        *content: ContentBuilder,
        jinja: Environment,
        style: RaspberryMintColorStyle,
    ):
        super().__init__(jinja=jinja)
        self._content = tuple(content)
        self._style = style

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, config: ColorStyleConfig, /) -> Self:
        content, jinja = await gather(
            gather(
                *map(
                    lambda manufacturer: new(manufacturer, project),
                    config.content,
                )
            ),
            project.jinja,
        )
        return cls(*content, jinja=jinja, style=config.style)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        content = await build(document, self._content)
        if content is None:
            return None
        return "component/raspberry-mint/color-style.html.j2", {
            "color_style": self._style.value,
            "color_style_content": content,
        }
