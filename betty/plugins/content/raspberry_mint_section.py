"""
The section content plugin.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING, Self, final, override

from betty.attr import Attr, Optional
from betty.attrs.localizable import LocalizableAttr
from betty.attrs.machine_name import MachineNameAttr
from betty.attrs.plugin_manufacturer_sequence import (
    PluginManufacturerSequenceAttr,
)
from betty.content import Content, ContentDefinition, ContentManufacturer, build
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.bool import BoolDefinition
from betty.factory import DataManufacturable
from betty.locale.localizable.gettext import _
from betty.plugins.asset_directory.raspberry_mint import RASPBERRY_MINT
from betty.plugins.content.template import Template, TemplateBuild
from betty.project import Project
from betty.sample import Sample, Size
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.document import Document
    from betty.jinja import Environment
    from betty.locale.localizable import ResolvableLocalizable
    from betty.machine_name import MachineName, ResolvableMachineName
    from betty.plugin.factory import ResolvablePluginManufacturerSequence


@final
@ObjectDefinition(
    label=_("Section configuration"),
    samples=[
        lambda: Sample(
            SectionData(
                ContentManufacturer("my-first-content"),
                heading=DUMMY_LOCALIZABLE,
            ),
            label="Minimal",
            size=Size.MINIMAL,
        ),
    ],
)
class SectionData(Data):
    """
    Configuration for :py:class:`betty.plugins.content.raspberry_mint_section.Section`.

    .. data:: betty.plugins.content.raspberry_mint_section:SectionData
    """

    content = PluginManufacturerSequenceAttr[ContentDefinition, Content](
        ContentManufacturer, label=_("Content")
    )
    """
    The content within this section.
    """

    heading = LocalizableAttr(label=_("Heading"))
    """
    The section heading.
    """

    name = Optional(MachineNameAttr())
    """
    The section's machine name, used to generate permanent links.
    """

    visually_hide_heading = Optional(
        Attr(
            BoolDefinition(label=_("Visually hide heading")),
            omit_load=True,
            omit_dump=lambda data: data is False,
        )
    )
    """
    Visually hide the heading.
    
    This keeps the heading for accessibility purposes, but does not display it visually.
    """

    def __init__(
        self,
        content: ResolvablePluginManufacturerSequence[ContentDefinition, Content],
        *,
        heading: ResolvableLocalizable,
        name: ResolvableMachineName | None = None,
        visually_hide_heading: bool | None = None,
    ):
        super().__init__()
        self.content = content
        self.heading = heading
        self.name = name
        self.visually_hide_heading = visually_hide_heading


@final
@ContentDefinition(
    "raspberry-mint-section",
    label=_("Section"),
    requires={Project.asset_directories.require(RASPBERRY_MINT)},
)
class Section(Template, DataManufacturable[SectionData]):
    """
    .. plugin:: content:raspberry-mint-section.
    """

    def __init__(
        self,
        /,
        content: Iterable[Content],
        *,
        heading: ResolvableLocalizable,
        name: MachineName | None = None,
        visually_hide_heading: bool | None = None,
        jinja: Environment,
    ):
        super().__init__(jinja=jinja)
        self._content = tuple(content)
        self._heading = heading
        self._name = name
        self._visually_hide_heading = bool(visually_hide_heading)

    @override
    @classmethod
    def new_data_cls(cls) -> type[SectionData]:
        return SectionData

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, data: SectionData, /) -> Self:
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
            heading=data.heading,
            jinja=jinja,
            name=data.name,
            visually_hide_heading=data.visually_hide_heading,
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
