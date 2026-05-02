"""
Place names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.entity import Entity, EntityDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localizable.static import STATIC_TRANSLATIONS_SCHEMA
from betty.properties.date import HasAnyDate
from betty.properties.localizable import LocalizableProperty

if TYPE_CHECKING:
    from betty.date import AnyDate

if TYPE_CHECKING:
    from betty.json_schema import Schema
    from betty.locale.localizable import ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project


@final
@EntityDefinition(
    "place-name",
    label=_("Place name"),
    label_plural=_("Place names"),
    label_countable=ngettext("{count} place name", "{count} place names"),
    public_facing=False,
)
class PlaceName(HasAnyDate, Entity):
    """
    .. plugin:: entity:place-name.
    """

    name = LocalizableProperty(label=_("Name"))

    def __init__(
        self,
        name: ResolvableLocalizable,
        *,
        date: AnyDate | None = None,
    ):
        super().__init__(date=date)
        self.name = name

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> Schema:
        schema = await super().linked_data_schema(project)
        schema.add_property("name", STATIC_TRANSLATIONS_SCHEMA)
        return schema

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable = await super().dump_linked_data(project)
        portable["name"] = dump_linked_data(
            self.name, localizers=await project.public_localizers
        )
        return portable
