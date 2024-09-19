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

    Enclosures describe the outer (```enclosed_by`) and inner(``encloses``) places, and their relationship.
    """

    _plugin_id = "enclosure"
    _plugin_label = _("Enclosure")

    #: The outer place.
    enclosed_by = ManyToOne["Enclosure", "Place"](
        "betty.ancestry.enclosure:Enclosure",
        "enclosed_by",
        "betty.ancestry:Place",
        "encloses",
    )
    #: The inner place.
    encloses = ManyToOne["Enclosure", "Place"](
        "betty.ancestry.enclosure:Enclosure",
        "encloses",
        "betty.ancestry:Place",
        "enclosed_by",
    )

    def __init__(
        self,
        encloses: Place | None = None,
        enclosed_by: Place | None = None,
    ):
        super().__init__()
        self.encloses = encloses
        self.enclosed_by = enclosed_by

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Enclosures")
