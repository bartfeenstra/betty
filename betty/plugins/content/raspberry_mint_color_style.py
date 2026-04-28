"""
The color style content plugin.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty.content import Content, ContentDefinition, ContentManufacturer, build
from betty.data import Data
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.enum import EnumDefinition
from betty.factory import DataManufacturable
from betty.locale.localizable.gettext import _
from betty.plugin.data.property import PluginManufacturerSequenceProperty
from betty.plugins.asset_directory.raspberry_mint import RASPBERRY_MINT
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.extension.raspberry_mint import ColorStyle as RaspberryMintColorStyle
from betty.project import Project
from betty.property import Property
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
            ColorStyleConfiguration(
                "my-first-content", style=RaspberryMintColorStyle.DARK
            ),
            label="Default",
        )
    ],
)
class ColorStyleConfiguration(Data):
    """
    Configuration for :py:class:`betty.plugins.content.raspberry_mint_color_style.ColorStyle`.

    .. data:: betty.plugins.content.raspberry_mint_color_style:ColorStyleConfiguration
    """

    content = PluginManufacturerSequenceProperty[ContentDefinition, Content](
        ContentManufacturer, label=_("Content")
    )
    """
    The content within this color style.
    """

    style = Property(EnumDefinition(cls=RaspberryMintColorStyle, label=_("Style")))
    """
    The style.
    """

    def __init__(
        self,
        content: ResolvablePluginManufacturerSequence[ContentDefinition, Content],
        *,
        style: RaspberryMintColorStyle,
    ):
        super().__init__()
        self.style = style
        self.content = content


@final
@ContentDefinition(
    "raspberry-mint-color-style",
    label=_("Color style"),
    requires={Project.asset_directories.require(RASPBERRY_MINT)},
)
class ColorStyle(Template, DataManufacturable[ColorStyleConfiguration]):
    """
    Change the color style for all containing content.

    .. plugin:: content:raspberry-mint-color-style
    """

    def __init__(
        self,
        /,
        content: Iterable[Content],
        *,
        jinja: Environment,
        style: RaspberryMintColorStyle,
    ):
        super().__init__(jinja=jinja)
        self._content = tuple(content)
        self._style = style

    @override
    @classmethod
    def new_data_cls(cls) -> type[ColorStyleConfiguration]:
        return ColorStyleConfiguration

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, data: ColorStyleConfiguration, /) -> Self:
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
