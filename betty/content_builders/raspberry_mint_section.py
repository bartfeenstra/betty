"""
The section content plugin.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.attrs.localizable import new_localizable_attr
from betty.attrs.machine_name import new_machine_name_attr
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
from betty.datas.bool import BoolDefinition
from betty.localizables.gettext import _
from betty.plugin.factory import ConfigurableIntegratable, new
from betty.project import Project
from betty.prop import HasProps
from betty.sample import Sample, Size

if TYPE_CHECKING:
    from betty.document import Document
    from betty.jinja import Environment
    from betty.localizable import ResolvableLocalizable
    from betty.machine_name import MachineName, ResolvableMachineName


@final
@ObjectDefinition(
    label=_("Section configuration"),
    samples=[
        lambda: Sample(
            SectionConfig(
                NewContentBuilder("my-first-content"),
                heading="-",
            ),
            label="Minimal",
            size=Size.MINIMAL,
        ),
    ],
    manufacturer=lambda **fields: SectionConfig(*fields.pop("content"), **fields),
)
class SectionConfig(Data, HasProps):
    """
    Configuration for :py:class:`betty.content_builders.raspberry_mint_section.Section`.

    .. data:: betty.content_builders.raspberry_mint_section:SectionData
    """

    content = new_new_plugin_sequence_attr(NewContentBuilder, label=_("Content"))
    """
    The content within this section.
    """

    heading = new_localizable_attr(label=_("Heading"))
    """
    The section heading.
    """

    name = new_machine_name_attr().optional
    """
    The section's machine name, used to generate permanent links.
    """

    visually_hide_heading = OwnerAttr(
        BoolDefinition(label=_("Visually hide heading"))
    ).default(lambda: False)
    """
    Visually hide the heading.
    
    This keeps the heading for accessibility purposes, but does not display it visually.
    """

    def __init__(
        self,
        *content: ResolvableContentBuilderManufacturer,
        heading: ResolvableLocalizable,
        name: ResolvableMachineName | None = None,
        visually_hide_heading: bool = False,
    ):
        super().__init__()
        self.content = content
        self.heading = heading
        self.name = name
        self.visually_hide_heading = visually_hide_heading


@final
@ContentBuilderDefinition(
    "raspberry-mint-section",
    label=_("Section"),
    config_cls=SectionConfig,
    requires={Project.asset_directories.require(raspberry_mint)},
)
class Section(Template, ConfigurableIntegratable[SectionConfig]):
    """
    .. plugin:: content-builder:raspberry-mint-section.
    """

    def __init__(
        self,
        /,
        *content: ContentBuilder,
        heading: ResolvableLocalizable,
        name: MachineName | None = None,
        visually_hide_heading: bool = False,
        jinja: Environment,
    ):
        super().__init__(jinja=jinja)
        self._content = tuple(content)
        self._heading = heading
        self._name = name
        self._visually_hide_heading = bool(visually_hide_heading)

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, config: SectionConfig, /) -> Self:
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
            heading=config.heading,
            jinja=jinja,
            name=config.name,
            visually_hide_heading=config.visually_hide_heading,
        )

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        content = await build(document, self._content)
        if content is None:
            return None
        return "component/raspberry-mint/section.html.j2", {
            "section_content": content,
            "section_heading": self._heading,
            "section_name": self._name,
            "section_visually_hide_heading": self._visually_hide_heading,
        }
