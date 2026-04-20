"""
Provide the place entity.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, final, override

from betty.entity import EntityDefinition
from betty.entity.association import BidirectionalToManySingleType, ToManyAssociates
from betty.entity.has_file_references import HasFileReferences
from betty.entity.has_links import HasLinks
from betty.entity.has_notes import HasNotes
from betty.json.linked_data import JsonLdObject, dump_context
from betty.json.schema import Array, Number, Object
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.entity.place_name import PlaceName
from betty.plugins.place_type.unknown import Unknown as UnknownPlaceType
from betty.privacy import HasPrivacy

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableSequence

    from geopy import Point

    from betty.locale.localizable import Localizable
    from betty.place_type import PlaceType
    from betty.plugins.entity.enclosure import Enclosure
    from betty.plugins.entity.event import Event
    from betty.plugins.entity.link import Link
    from betty.plugins.entity.note import Note
    from betty.portable import PortableMapping
    from betty.privacy import Privacy
    from betty.project import Project


@final
@EntityDefinition(
    "place",
    label=_("Place"),
    label_plural=_("Places"),
    label_countable=ngettext("{count} place", "{count} places"),
)
class Place(HasLinks, HasFileReferences, HasNotes, HasPrivacy):
    """
    .. plugin:: entity:place.
    """

    events = BidirectionalToManySingleType["Place", "Event"](
        "betty.plugins.entity.event:Event",
        "place",
        label=_("Events"),
        description=_("The events that happened in this place"),
    )
    """
    The events that happened here.
    """

    enclosers = BidirectionalToManySingleType["Place", "Enclosure"](
        "betty.plugins.entity.enclosure:Enclosure",
        "enclosee",
        label=_("Enclosers"),
        description=_("The places this place is enclosed or contained by"),
        linked_data_embedded=True,
    )
    """
    Other places containing this one.
    """

    enclosees = BidirectionalToManySingleType["Place", "Enclosure"](
        "betty.plugins.entity.enclosure:Enclosure",
        "encloser",
        label=_("Enclosees"),
        description=_("The places this place encloses or contains"),
        linked_data_embedded=True,
    )
    """
    Other places contained by this one.
    """

    def __init__(
        self,
        *,
        id: str | None = None,  # noqa: A002
        names: Iterable[PlaceName] = (),
        events: ToManyAssociates[Event] = (),
        enclosers: ToManyAssociates[Enclosure] = (),
        enclosees: ToManyAssociates[Enclosure] = (),
        notes: ToManyAssociates[Note] = (),
        coordinates: Point | None = None,
        links: ToManyAssociates[Link] = (),
        privacy: Privacy | None = None,
        place_type: PlaceType | None = None,
    ):
        super().__init__(id, notes=notes, links=links, privacy=privacy)
        self._names = list(names)
        self._coordinates = coordinates
        self.events = events
        self.enclosers = enclosers
        self.enclosees = enclosees
        self._place_type = place_type or UnknownPlaceType()

    @property
    def place_type(self) -> PlaceType:
        """
        The type of this place.
        """
        return self._place_type

    @place_type.setter
    def place_type(self, place_type: PlaceType) -> None:
        self._place_type = place_type

    @property
    def names(self) -> MutableSequence[PlaceName]:
        """
        The place's names.

        The first name is considered the :py:attr:`place label <betty.plugins.entity.place.Place.label>`.
        """
        return self._names

    @property
    def coordinates(self) -> Point | None:
        """
        The place's coordinates.
        """
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates: Point) -> None:
        self._coordinates = coordinates

    @override
    @property
    def label(self) -> Localizable:
        with suppress(IndexError):
            return self.names[0].name
        return super().label

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable = await super().dump_linked_data(project)
        dump_context(
            portable,
            names="https://schema.org/name",
            events="https://schema.org/event",
            enclosers="https://schema.org/containedInPlace",
            enclosees="https://schema.org/containsPlace",
        )
        portable["@type"] = "https://schema.org/Place"
        portable["names"] = [
            await name.dump_linked_data(project) for name in self.names
        ]
        if self.coordinates is not None:
            portable_coordinates: PortableMapping = {
                "@type": "https://schema.org/GeoCoordinates",
                "latitude": self.coordinates.latitude,
                "longitude": self.coordinates.longitude,
            }
            dump_context(portable, coordinates="https://schema.org/geo")
            dump_context(portable_coordinates, latitude="https://schema.org/latitude")
            dump_context(portable_coordinates, longitude="https://schema.org/longitude")
            portable["coordinates"] = portable_coordinates
        return portable

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "names", Array(await PlaceName.linked_data_schema(project), title="Names")
        )
        coordinate_schema = Number(title="Coordinate")
        coordinates_schema = Object(title="Coordinates")
        coordinates_schema.add_property("latitude", coordinate_schema, False)
        coordinates_schema.add_property("longitude", coordinate_schema, False)
        schema.add_property("coordinates", coordinates_schema, False)
        return schema
