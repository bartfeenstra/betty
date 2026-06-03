"""
Data types to describe the relationships between places.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.attrs.date import HasAnyDate
from betty.entity import Entity, EntityDefinition
from betty.entity.association import BidirectionalToOne, ToOneAssociate
from betty.entity.has_citations import HasCitations
from betty.locale.localizable.gettext import _, ngettext

if TYPE_CHECKING:
    from betty.entities.place import Place


@final
@EntityDefinition(
    "enclosure",
    label=_("Enclosure"),
    label_plural=_("Enclosures"),
    label_countable=ngettext("{count} enclosure", "{count} enclosures"),
    public_facing=False,
)
class Enclosure(HasAnyDate, HasCitations, Entity):
    """
    .. plugin:: entity:enclosure.
    """

    encloser = BidirectionalToOne["Enclosure", "Place"](
        "betty.entities.place:Place",
        "enclosees",
        label=_("Encloser"),
        description=_("The place that encloses or contains the enclosee"),
    )
    """
    The outer place.
    """

    enclosee = BidirectionalToOne["Enclosure", "Place"](
        "betty.entities.place:Place",
        "enclosers",
        label=_("Enclosee"),
        description=_("The place that is enclosed or contained by the encloser"),
    )
    """
    The inner place.
    """

    def __init__(
        self, enclosee: ToOneAssociate[Place], encloser: ToOneAssociate[Place]
    ):
        super().__init__()
        self.enclosee = enclosee
        self.encloser = encloser
