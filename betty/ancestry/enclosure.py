"""
Data types to describe the relationships between places.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.ancestry.date import HasDate
from betty.ancestry.has_citations import HasCitations
from betty.locale.localizable import _, ngettext
from betty.model import Entity, EntityDefinition
from betty.model.association import BidirectionalToOne, ToOneAssociate

if TYPE_CHECKING:
    from betty.ancestry.place import Place


@final
@EntityDefinition(
    id="enclosure",
    label=_("Enclosure"),
    label_plural=_("Enclosures"),
    label_countable=ngettext("{count} enclosure", "{count} enclosures"),
    public_facing=False,
)
class Enclosure(HasDate, HasCitations, Entity):
    """
    The enclosure of one place by another.

    Enclosures describe the outer (```encloser`) and inner(``enclosee``) places, and their relationship.
    """

    #: The outer place.
    encloser = BidirectionalToOne["Enclosure", "Place"](
        "betty.ancestry.enclosure:Enclosure",
        "encloser",
        "betty.ancestry.place:Place",
        "enclosee",
        title="Encloser",
        description="The place that encloses or contains the enclosee",
    )
    #: The inner place.
    enclosee = BidirectionalToOne["Enclosure", "Place"](
        "betty.ancestry.enclosure:Enclosure",
        "enclosee",
        "betty.ancestry.place:Place",
        "encloser",
        title="Enclosee",
        description="The place that is enclosed or contained by the encloser",
    )

    def __init__(
        self, enclosee: ToOneAssociate[Place], encloser: ToOneAssociate[Place]
    ):
        super().__init__()
        self.enclosee = enclosee
        self.encloser = encloser
