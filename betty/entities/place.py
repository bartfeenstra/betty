"""
Provide the place entity.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Self, final, override

from betty.associations.has_file_references import HasFileReferences
from betty.associations.has_links import HasLinks
from betty.associations.has_notes import HasNotes
from betty.associations.to_many import ToMany, ToManyAssociates
from betty.entities.enclosure import Enclosure
from betty.entities.place_name import PlaceName
from betty.entity import EntityDefinition
from betty.linked_data import LinkedData
from betty.localizables.gettext import _, ngettext
from betty.place_types.unknown import UnknownPlaceType
from betty.privacy import Privacy
from betty.typing import Voidable, VoidableType

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from geopy import Point

    from betty.entities.event import Event
    from betty.entities.link import Link
    from betty.entities.note import Note
    from betty.localizable import Localizable
    from betty.machine_name import ResolvableMachineName
    from betty.place_type import PlaceType
    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.typing import VoidType


@final
@EntityDefinition(
    "place",
    label=_("Place"),
    label_plural=_("Places"),
    label_countable=ngettext("{count} place", "{count} places"),
    linked_data_type="https://schema.org/Place",
)
class Place(HasLinks, HasFileReferences, HasNotes):
    """
    .. plugin:: entity:place.
    """

    events = ToMany[Self, "Event"](
        "betty.entities.event:Event",
        "place",
        label=_("Events"),
        description=_("The events that happened in this place"),
        linked_data_context="https://schema.org/event",
    )
    """
    The events that happened here.
    """

    enclosers = ToMany[Self, Enclosure](
        Enclosure,
        "enclosee",
        label=_("Enclosers"),
        description=_("The places this place is enclosed or contained by"),
        linked_data_context="https://schema.org/containedInPlace",
    )
    """
    Other places containing this one.
    """

    enclosees = ToMany[Self, Enclosure](
        Enclosure,
        "encloser",
        label=_("Enclosees"),
        description=_("The places this place encloses or contains"),
        linked_data_context="https://schema.org/containsPlace",
    )
    """
    Other places contained by this one.
    """

    names = ToMany[Self, PlaceName](
        PlaceName,
        "place",
        label=_("Names"),
        linked_data_context="https://schema.org/name",
    )
    """
    The place's names.

    The first name is considered the :py:attr:`place label <betty.entities.place.Place.label>`.
    """

    def __init__(
        self,
        *,
        id: ResolvableMachineName | None = None,  # noqa: A002
        names: Iterable[PlaceName] = (),
        events: ToManyAssociates[Self, Event] = (),
        enclosers: ToManyAssociates[Self, Enclosure] = (),
        enclosees: ToManyAssociates[Self, Enclosure] = (),
        notes: ToManyAssociates[Self, Note] = (),
        coordinates: Point | None = None,
        links: ToManyAssociates[Self, Link] = (),
        privacy: Privacy = Privacy.UNDETERMINED,
        place_type: PlaceType | None = None,
    ):
        super().__init__(id=id, notes=notes, links=links, privacy=privacy)
        self.names = names
        self.coordinates = coordinates
        """
        The place's coordinates.
        """
        self.events = events
        self.enclosers = enclosers
        self.enclosees = enclosees
        self.place_type = place_type or UnknownPlaceType()
        """
        The type of this place.
        """

    @override
    @property
    def label(self) -> Localizable:
        with suppress(IndexError):
            return self.names[0].name
        return super().label

    @override
    @classmethod
    async def linked_data_schema_properties(
        cls, project: Project, /
    ) -> Mapping[str, VoidableType[PortableMapping]]:
        coordinate_schema = {
            "title": "Coordinate",
            "type": "number",
        }
        return {
            "coordinates": Voidable({
                "additionalProperties": False,
                "properties": {
                    "latitude": coordinate_schema,
                    "longitude": coordinate_schema,
                },
                "title": "Coordinates",
                "type": "object",
            })
        }

    @override
    async def dump_linked_data_properties(
        self, project: Project, /
    ) -> Mapping[str, LinkedData | VoidType]:
        if self.private:
            return {}
        return {
            "coordinates": LinkedData(
                {
                    "@type": "https://schema.org/GeoCoordinates",
                    "@context": {
                        "latitude": "https://schema.org/latitude",
                        "longitude": "https://schema.org/longitude",
                    },
                    "latitude": self.coordinates.latitude,
                    "longitude": self.coordinates.longitude,
                },
                context="https://schema.org/geo",
            )
        }
