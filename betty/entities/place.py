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
from betty.json_schema import Array, Number, Object
from betty.linked_data import JsonLdObject, dump_context
from betty.localizables.gettext import _, ngettext
from betty.place_types.unknown import UnknownPlaceType
from betty.privacy import Privacy

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableSequence

    from geopy import Point

    from betty.entities.event import Event
    from betty.entities.link import Link
    from betty.entities.note import Note
    from betty.localizable import Localizable
    from betty.machine_name import ResolvableMachineName
    from betty.place_type import PlaceType
    from betty.portable import PortableMapping
    from betty.project import Project


@final
@EntityDefinition(
    "place",
    label=_("Place"),
    label_plural=_("Places"),
    label_countable=ngettext("{count} place", "{count} places"),
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
    )
    """
    The events that happened here.
    """

    enclosed_by = ToMany[Self, Enclosure](
        Enclosure,
        "encloses",
        label=_("Enclosed by"),
        description=_("Other places that enclose this place"),
    )
    """
    Other places that enclose this place.
    """

    encloses = ToMany[Self, Enclosure](
        Enclosure,
        "enclosed_by",
        label=_("Encloses"),
        description=_("Other places this place encloses"),
    )
    """
    Other places this place encloses.
    """

    def __init__(
        self,
        *,
        id: ResolvableMachineName | None = None,  # noqa: A002
        names: Iterable[PlaceName] = (),
        events: ToManyAssociates[Self, Event] = (),
        enclosed_by: ToManyAssociates[Self, Enclosure] = (),
        encloses: ToManyAssociates[Self, Enclosure] = (),
        notes: ToManyAssociates[Self, Note] = (),
        coordinates: Point | None = None,
        links: ToManyAssociates[Self, Link] = (),
        privacy: Privacy = Privacy.UNDETERMINED,
        place_type: PlaceType | None = None,
    ):
        super().__init__(id=id, notes=notes, links=links, privacy=privacy)
        self._names = list(names)
        self.coordinates = coordinates
        """
        The place's coordinates.
        """
        self.events = events
        self.enclosed_by = enclosed_by
        self.encloses = encloses
        self.place_type = place_type or UnknownPlaceType()
        """
        The type of this place.
        """

    @property
    def names(self) -> MutableSequence[PlaceName]:
        """
        The place's names.

        The first name is considered the :py:attr:`place label <betty.entities.place.Place.label>`.
        """
        return self._names

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
            enclosedBy="https://schema.org/containedInPlace",
            encloses="https://schema.org/containsPlace",
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
