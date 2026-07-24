"""
Data types to describe the relationships between places.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from betty.associations.has_citations import HasCitations
from betty.associations.to_one import ToOne, ToOneAssociate
from betty.attrs.date import HasDate
from betty.entity import Entity, EntityDefinition
from betty.localizables.gettext import _, ngettext

if TYPE_CHECKING:
    from betty.entities.place import Place
    from betty.machine_name import ResolvableMachineName


@final
@EntityDefinition(
    "enclosure",
    label=_("Enclosure"),
    label_plural=_("Enclosures"),
    label_countable=ngettext("{count} enclosure", "{count} enclosures"),
    public_facing=False,
)
class Enclosure(HasDate, HasCitations, Entity):
    """
    .. plugin:: entity:enclosure.
    """

    enclosed_by = ToOne[Self, "Place"](
        "betty.entities.place:Place",
        "encloses",
        label=_("Enclosed by"),
        description=_("The place that encloses the other place"),
    )
    """
    The place that encloses the other place.
    """

    encloses = ToOne[Self, "Place"](
        "betty.entities.place:Place",
        "enclosed_by",
        label=_("Encloses"),
        description=_("The place that is enclosed by the other place"),
    )
    """
    The place that is enclosed by the other place.
    """

    def __init__(
        self,
        *,
        enclosed_by: ToOneAssociate[Self, Place],
        encloses: ToOneAssociate[Self, Place],
        id: ResolvableMachineName | None = None,  # noqa: A002
    ):
        super().__init__(id=id)
        self.enclosed_by = enclosed_by
        self.encloses = encloses
