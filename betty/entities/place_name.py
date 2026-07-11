"""
Place names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from betty.associations.to_one import ToOne, ToOneAssociate
from betty.attrs.date import HasAnyDate
from betty.attrs.localizable import new_localizable_attr
from betty.entity import Entity, EntityDefinition
from betty.localizables.gettext import _, ngettext

if TYPE_CHECKING:
    from betty.date import AnyDate
    from betty.entities.place import Place
    from betty.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName


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
