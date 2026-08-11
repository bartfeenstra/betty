from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

import pytest
from geopy import Point

from betty.associations.to_one import MissingAssociate, Placeholder
from betty.entities.enclosure import Enclosure
from betty.entities.event import Event
from betty.entities.link import Link
from betty.entities.place import Place
from betty.entities.place_name import PlaceName
from betty.entity import Entity
from betty.event_types.birth import Birth
from betty.locale import default_locale_tag
from betty.place_types.hamlet import Hamlet
from betty.place_types.unknown import UnknownPlaceType
from betty.test_utils.entity import EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.test_utils.conftest import AssertDumpsLinkedData


class TestPlace(EntityTestBase):
    @staticmethod
    def _sut_params() -> Sequence[Entity]:
        return [
            Place(),
            Place(names=[PlaceName("My First Place")]),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> Entity:
        return cast(Entity, request.param)

    def test_place_type__default(self) -> None:
        sut = Place()
        assert isinstance(sut.place_type, UnknownPlaceType)

    def test___init____with_events(self) -> None:
        event = Event()
        sut = Place(events=[event])
        assert list(sut.events) == [event]
        assert event.place is sut

    def test___init____with_enclosed_by(self) -> None:
        enclosure = Enclosure(encloses=Placeholder, enclosed_by=Place())
        sut = Place(enclosed_by=[enclosure])
        assert list(sut.enclosed_by) == [enclosure]
        assert enclosure.encloses is sut

    def test___init____with_encloses(self) -> None:
        enclosure = Enclosure(encloses=Place(), enclosed_by=Placeholder)
        sut = Place(encloses=[enclosure])
        assert list(sut.encloses) == [enclosure]
        assert enclosure.enclosed_by is sut

    def test___init____with_place_type(self) -> None:
        place_type = Hamlet()
        sut = Place(place_type=place_type)
        assert sut.place_type is place_type

    def test_place_type(self) -> None:
        place_type = Hamlet()
        sut = Place()
        sut.place_type = place_type
        assert sut.place_type is place_type

    def test_events(self) -> None:
        sut = Place()
        event = Event()
        sut.events.add(event)
        assert event in sut.events
        assert sut == event.place
        sut.events.remove(event)
        assert list(sut.events) == []
        assert event.place is None

    def test_enclosed_by(self) -> None:
        sut = Place()
        assert list(sut.enclosed_by) == []
        enclosed_by = Place()
        enclosure = Enclosure(encloses=sut, enclosed_by=enclosed_by)
        assert enclosure in sut.enclosed_by
        assert sut == enclosure.encloses
        sut.enclosed_by.remove(enclosure)
        assert list(sut.enclosed_by) == []
        with pytest.raises(MissingAssociate):
            enclosure.encloses  # noqa: B018

    def test_encloses(self) -> None:
        sut = Place()
        assert list(sut.encloses) == []
        encloses = Place()
        enclosure = Enclosure(encloses=encloses, enclosed_by=sut)
        assert enclosure in sut.encloses
        assert sut == enclosure.enclosed_by
        sut.encloses.remove(enclosure)
        assert list(sut.encloses) == []
        with pytest.raises(MissingAssociate):
            enclosure.enclosed_by  # noqa: B018

    def test_id(self) -> None:
        sut = Place(id="my-first-place")
        assert sut.id == "my-first-place"

    def test_links(self) -> None:
        sut = Place()
        assert list(sut.links) == []

    def test_names(self) -> None:
        sut = Place()
        assert sut.names is sut.names

    def test_coordinates(self) -> None:
        sut = Place()
        coordinates = Point()
        sut.coordinates = coordinates
        assert sut.coordinates == coordinates

    async def test_dump_linked_data__should_dump_minimal(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        place = Place(id="my-first-place")
        expected: Mapping[str, Any] = {
            "@context": {
                "names": "https://schema.org/name",
                "enclosedBy": "https://schema.org/containedInPlace",
                "encloses": "https://schema.org/containsPlace",
                "events": "https://schema.org/event",
            },
            "@id": "https://example.com/place/my-first-place/index.json",
            "@type": "https://schema.org/Place",
            "id": "my-first-place",
            "names": [],
            "enclosedBy": [],
            "encloses": [],
            "events": [],
            "notes": [],
            "links": [],
            "privacy": False,
            "files": [],
        }
        actual = await assert_dumps_linked_data(place)
        assert actual == expected

    async def test_dump_linked_data__should_dump_full(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        name = "The Place"
        place_name = PlaceName(name, id="my-first-place-name")
        latitude = 12.345
        longitude = -54.321
        coordinates = Point(latitude, longitude)
        link = Link("https://example.com/the-place", id="my-first-link")
        link.label = "The Place Online"
        place = Place(
            id="my-first-place",
            names=[place_name],
            events=[
                Event(
                    id="my-first-event",
                    event_type=Birth(),
                )
            ],
            links=[link],
        )
        place.coordinates = coordinates
        Enclosure(
            encloses=place,
            enclosed_by=Place(id="the-enclosing-place"),
            id="the-enclosing-enclosure",
        )
        Enclosure(
            encloses=Place(id="the-enclosed-place"),
            enclosed_by=place,
            id="the-enclosed-enclosure",
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "names": "https://schema.org/name",
                "enclosedBy": "https://schema.org/containedInPlace",
                "encloses": "https://schema.org/containsPlace",
                "events": "https://schema.org/event",
                "coordinates": "https://schema.org/geo",
            },
            "@id": "https://example.com/place/my-first-place/index.json",
            "@type": "https://schema.org/Place",
            "id": "my-first-place",
            "names": [
                {
                    "@id": "https://example.com/place-name/my-first-place-name/index.json",
                    "id": "my-first-place-name",
                    "name": {default_locale_tag: name},
                    "privacy": False,
                }
            ],
            "events": [
                "/event/my-first-event/index.json",
            ],
            "notes": [],
            "links": [
                "/link/my-first-link/index.json",
            ],
            "coordinates": {
                "@context": {
                    "latitude": "https://schema.org/latitude",
                    "longitude": "https://schema.org/longitude",
                },
                "@type": "https://schema.org/GeoCoordinates",
                "latitude": latitude,
                "longitude": longitude,
            },
            "encloses": [
                "/enclosure/the-enclosed-enclosure/index.json",
            ],
            "enclosedBy": [
                "/enclosure/the-enclosing-enclosure/index.json",
            ],
            "privacy": False,
            "files": [],
        }
        actual = await assert_dumps_linked_data(place)
        assert actual == expected
