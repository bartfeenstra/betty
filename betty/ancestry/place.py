"""
Provide the place entity.
"""

from __future__ import annotations

from contextlib import suppress
from typing import final, MutableSequence, Iterable, Iterator, TYPE_CHECKING
from urllib.parse import quote

from typing_extensions import override


from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.link import HasLinks, Link
from betty.ancestry.name import Name
from betty.ancestry.note import HasNotes, Note
from betty.ancestry.place_type.place_types import Unknown as UnknownPlaceType
from betty.json.linked_data import dump_context, JsonLdObject
from betty.json.schema import Object, Array, Number
from betty.locale.localizable import _, Localizable
from betty.model import (
    UserFacingEntity,
    Entity,
    GeneratedEntityId,
    EntityReferenceCollectionSchema,
)
from betty.model.association import OneToMany
from betty.plugin import ShorthandPluginBase
from betty.ancestry.privacy import HasPrivacy

if TYPE_CHECKING:
    from betty.ancestry import Event
    from betty.ancestry.enclosure import Enclosure
    from betty.ancestry.place_type import PlaceType
    from betty.ancestry.privacy import Privacy
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

    events = OneToMany["Place", "Event"](
        "betty.ancestry:Place", "events", "betty.ancestry:Event", "place"
    )
    enclosed_by = OneToMany["Place", "Enclosure"](
        "betty.ancestry:Place",
        "enclosed_by",
        "betty.ancestry.enclosure:Enclosure",
        "encloses",
    )
    encloses = OneToMany["Place", "Enclosure"](
        "betty.ancestry:Place",
        "encloses",
        "betty.ancestry.enclosure:Enclosure",
        "enclosed_by",
    )

    def __init__(
        self,
        *,
        id: str | None = None,  # noqa A002
        names: MutableSequence[Name] | None = None,
        events: Iterable[Event] | None = None,
        enclosed_by: Iterable["Enclosure"] | None = None,
        encloses: Iterable["Enclosure"] | None = None,
        notes: Iterable[Note] | None = None,
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
        if enclosed_by is not None:
            self.enclosed_by = enclosed_by
        if encloses is not None:
            self.encloses = encloses
        self._place_type = place_type or UnknownPlaceType()

    @property
    def walk_encloses(self) -> Iterator["Enclosure"]:
        """
        All enclosed places.
        """
        for enclosure in self.encloses:
            yield enclosure
            if enclosure.encloses is not None:
                yield from enclosure.encloses.walk_encloses

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

        The first name is considered the :py:attr:`place label <betty.ancestry.Place.label>`.
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
            return self.names[0]
        return super().label

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump_context(
            dump,
            names="https://schema.org/name",
            events="https://schema.org/event",
            enclosedBy="https://schema.org/containedInPlace",
            encloses="https://schema.org/containsPlace",
        )
        dump["@type"] = "https://schema.org/Place"
        dump["names"] = [await name.dump_linked_data(project) for name in self.names]
        dump["events"] = [
            project.static_url_generator.generate(
                f"/event/{quote(event.id)}/index.json"
            )
            for event in self.events
            if not isinstance(event.id, GeneratedEntityId)
        ]
        dump["enclosedBy"] = [
            project.static_url_generator.generate(
                f"/place/{quote(enclosure.enclosed_by.id)}/index.json"
            )
            for enclosure in self.enclosed_by
            if enclosure.enclosed_by is not None
            and not isinstance(enclosure.enclosed_by.id, GeneratedEntityId)
        ]
        dump["encloses"] = [
            project.static_url_generator.generate(
                f"/place/{quote(enclosure.encloses.id)}/index.json"
            )
            for enclosure in self.encloses
            if enclosure.encloses is not None
            and not isinstance(enclosure.encloses.id, GeneratedEntityId)
        ]
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
    async def linked_data_schema(cls, project: Project) -> Object:
        from betty.ancestry import Event

        schema = await super().linked_data_schema(project)
        schema.add_property(
            "names", Array(await Name.linked_data_schema(project), title="Names")
        )
        schema.add_property("enclosedBy", EntityReferenceCollectionSchema(Place))
        schema.add_property("encloses", EntityReferenceCollectionSchema(Place))
        coordinate_schema = Number(title="Coordinate")
        coordinates_schema = JsonLdObject(title="Coordinates")
        coordinates_schema.add_property("latitude", coordinate_schema, False)
        coordinates_schema.add_property("longitude", coordinate_schema, False)
        schema.add_property("coordinates", coordinates_schema, False)
        schema.add_property("events", EntityReferenceCollectionSchema(Event))
        return schema
