"""
Data types to describe the relationships between places.
"""

from __future__ import annotations

from typing import final, TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.date import HasDate
from betty.ancestry.has_citations import HasCitations
from betty.locale.localizable import _, Localizable
from betty.model import Entity
from betty.model.association import ManyToOne
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    from betty.ancestry.place import Place


@final
class Enclosure(ShorthandPluginBase, HasDate, HasCitations, Entity):
    """
    The enclosure of one place by another.

    Enclosures describe the outer (```encloser`) and inner(``enclosee``) places, and their relationship.
    """

    _plugin_id = "enclosure"
    _plugin_label = _("Enclosure")

    #: The outer place.
    encloser = ManyToOne["Enclosure", "Place"](
        "betty.ancestry.enclosure:Enclosure",
        "encloser",
        "betty.ancestry.place:Place",
        "enclosee",
    )
    #: The inner place.
    enclosee = ManyToOne["Enclosure", "Place"](
        "betty.ancestry.enclosure:Enclosure",
        "enclosee",
        "betty.ancestry.place:Place",
        "encloser",
    )

    def __init__(
        self,
        enclosee: Place | None = None,
        encloser: Place | None = None,
    ):
        super().__init__()
        self.enclosee = enclosee
        self.encloser = encloser

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Enclosures")
