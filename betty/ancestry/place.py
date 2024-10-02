"""
Provide the place entity.
"""

from __future__ import annotations

from contextlib import suppress
from typing import final, MutableSequence, Iterable, Iterator, TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_notes import HasNotes
from betty.ancestry.link import HasLinks, Link
from betty.ancestry.name import Name
from betty.ancestry.place_type.place_types import Unknown as UnknownPlaceType
from betty.json.linked_data import dump_context, JsonLdObject
from betty.json.schema import Array, Number, Object
from betty.locale.localizable import _, Localizable
from betty.model import UserFacingEntity, Entity
from betty.model.association import BidirectionalToMany, ToManyResolver
from betty.plugin import ShorthandPluginBase
from betty.privacy import HasPrivacy

if TYPE_CHECKING:
    from betty.ancestry.note import Note
    from betty.ancestry.event import Event
    from betty.ancestry.enclosure import Enclosure
    from betty.ancestry.place_type import PlaceType
    from betty.privacy import Privacy
    from geopy import Point
    from betty.project import Project
    from betty.serde.dump import DumpMapping, Dump


@final
class Place(
    ShorthandPluginBase,
    HasLinks,
    HasFileReferences,
    HasNotes,
    HasPrivacy,
    UserFacingEntity,
    Entity,
):
    """
    A place.

    A place is a physical location on earth. It may be identifiable by GPS coordinates only, or
    be a well-known city, with names in many languages, imagery, and its own Wikipedia page, or
    any type of place in between.
    """

    _plugin_id = "place"
    _plugin_label = _("Place")

    events = BidirectionalToMany["Place", "Event"](
        "betty.ancestry.place:Place",
        "events",
        "betty.ancestry.event:Event",
        "place",
        title="Events",
        description="The events that happened in this place",
    )
    enclosers = BidirectionalToMany["Place", "Enclosure"](
        "betty.ancestry.place:Place",
        "encloser",
        "betty.ancestry.enclosure:Enclosure",
        "enclosee",
        title="Enclosers",
        description="The places this place is enclosed or contained by",
        linked_data_embedded=True,
    )
    enclosees = BidirectionalToMany["Place", "Enclosure"](
        "betty.ancestry.place:Place",
        "enclosee",
        "betty.ancestry.enclosure:Enclosure",
        "encloser",
        title="Enclosees",
        description="The places this place encloses or contains",
        linked_data_embedded=True,
    )

    def __init__(
        self,
        *,
        id: str | None = None,  # noqa A002
        names: MutableSequence[Name] | None = None,
        events: Iterable[Event] | ToManyResolver[Event] | None = None,
        enclosers: Iterable["Enclosure"] | ToManyResolver["Enclosure"] | None = None,
        enclosees: Iterable["Enclosure"] | ToManyResolver["Enclosure"] | None = None,
        notes: Iterable[Note] | ToManyResolver[Note] | None = None,
        coordinates: Point | None = None,
        links: MutableSequence[Link] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        place_type: PlaceType | None = None,
    ):
        super().__init__(
            id,
            notes=notes,
            links=links,
            privacy=privacy,
            public=public,
            private=private,
        )
        self._names = [] if names is None else names
        self._coordinates = coordinates
        if events is not None:
            self.events = events
        if enclosers is not None:
            self.enclosers = enclosers
        if enclosees is not None:
            self.enclosees = enclosees
        self._place_type = place_type or UnknownPlaceType()

    @property
    def walk_enclosees(self) -> Iterator["Enclosure"]:
        """
        All enclosed places.
        """
        for enclosure in self.enclosees:
            yield enclosure
            yield from enclosure.enclosee.walk_enclosees

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Places")

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
    def names(self) -> MutableSequence[Name]:
        """
        The place's names.

        The first name is considered the :py:attr:`place label <betty.ancestry.place.Place.label>`.
        """
        return self._names

    @property
    def coordinates(self) -> Point | None:
        """
        The place's coordinates.
        """
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates: Point):
        self._coordinates = coordinates

    @override
    @property
    def label(self) -> Localizable:
        with suppress(IndexError):
            return self.names[0].name
        return super().label

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump_context(
            dump,
            names="https://schema.org/name",
            events="https://schema.org/event",
            enclosers="https://schema.org/containedInPlace",
            enclosees="https://schema.org/containsPlace",
        )
        dump["@type"] = "https://schema.org/Place"
        dump["names"] = [await name.dump_linked_data(project) for name in self.names]
        if self.coordinates is not None:
            dump["coordinates"] = {
                "@type": "https://schema.org/GeoCoordinates",
                "latitude": self.coordinates.latitude,
                "longitude": self.coordinates.longitude,
            }
            dump_context(dump, coordinates="https://schema.org/geo")
            dump_context(
                dump["coordinates"],  # type: ignore[arg-type]
                latitude="https://schema.org/latitude",
            )
            dump_context(
                dump["coordinates"],  # type: ignore[arg-type]
                longitude="https://schema.org/longitude",
            )
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "names", Array(await Name.linked_data_schema(project), title="Names")
        )
        coordinate_schema = Number(title="Coordinate")
        coordinates_schema = Object(title="Coordinates")
        coordinates_schema.add_property("latitude", coordinate_schema, False)
        coordinates_schema.add_property("longitude", coordinate_schema, False)
        schema.add_property("coordinates", coordinates_schema, False)
        return schema
