"""
Place names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.associations.to_one import ToOne, ToOneAssociate
from betty.attrs.date import HasAnyDate
from betty.attrs.localizable import new_localizable_attr
from betty.entity import Entity, EntityDefinition
from betty.json_schemas.static_translations import new_static_translations_schema
from betty.localizable.linked_data import dump_linked_data
from betty.localizables.gettext import _, ngettext

if TYPE_CHECKING:
    from betty.date import AnyDate
    from betty.entities.place import Place
    from betty.linked_data import LinkedData
    from betty.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.typing import VoidableType


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

    name = new_localizable_attr(label=_("Name"))

    place = ToOne[Self, "Place"](
        "betty.entities.place:Place",
        "names",
        label=_("Place"),
    )
    """
    The place whose name this is.
    """

    def __init__(
        self,
        name: ResolvableLocalizable,
        *,
        date: AnyDate | None = None,
        id: ResolvableMachineName | None = None,  # noqa: A002
        place: ToOneAssociate[Self, Place] | None = None,
    ):
        super().__init__(date=date, id=id)
        self.name = name
        if place:
            self.place = place

    @override
    @classmethod
    async def linked_data_schema(
        cls, project: Project, /
    ) -> VoidableType[PortableMapping]:
        schema = await super().linked_data_schema(project)
        schema.add_property("name", new_static_translations_schema())
        return schema

    @override
    async def dump_linked_data(self, project: Project, /) -> LinkedData:
        portable = await super().dump_linked_data(project)
        portable["name"] = dump_linked_data(
            self.name, localizers=await project.public_localizers
        )
        return portable
