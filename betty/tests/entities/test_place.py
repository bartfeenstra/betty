from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

import pytest
from geopy import Point

from betty.entities.enclosure import Enclosure
from betty.entities.event import Event
from betty.entities.link import Link
from betty.entities.place import Place
from betty.entities.place_name import PlaceName
from betty.entity import Entity
from betty.entity.association import AssociationRequired, TemporaryToOneResolver
from betty.event_types.birth import Birth
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG, to_language_tag
from betty.place_types.hamlet import Hamlet
from betty.place_types.unknown import Unknown as UnknownPlaceType
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

    def test___init____with_enclosers(self) -> None:
        enclosure = Enclosure(enclosee=TemporaryToOneResolver(), encloser=Place())
        sut = Place(enclosers=[enclosure])
        assert list(sut.enclosers) == [enclosure]
        assert enclosure.enclosee is sut

    def test___init____with_enclosees(self) -> None:
        enclosure = Enclosure(enclosee=Place(), encloser=TemporaryToOneResolver())
        sut = Place(enclosees=[enclosure])
        assert list(sut.enclosees) == [enclosure]
        assert enclosure.encloser is sut

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

    def test_enclosers(self) -> None:
        sut = Place()
        assert list(sut.enclosers) == []
        encloser = Place()
        enclosure = Enclosure(enclosee=sut, encloser=encloser)
        assert enclosure in sut.enclosers
        assert sut == enclosure.enclosee
        sut.enclosers.remove(enclosure)
        assert list(sut.enclosers) == []
        with pytest.raises(AssociationRequired):
            enclosure.enclosee  # noqa: B018

    def test_enclosees(self) -> None:
        sut = Place()
        assert list(sut.enclosees) == []
        enclosee = Place()
        enclosure = Enclosure(enclosee=enclosee, encloser=sut)
        assert enclosure in sut.enclosees
        assert sut == enclosure.encloser
        sut.enclosees.remove(enclosure)
        assert list(sut.enclosees) == []
        with pytest.raises(AssociationRequired):
            enclosure.encloser  # noqa: B018

    def test_id(self) -> None:
        place_id = "C1"
        sut = Place(id=place_id)
        assert sut.id == place_id

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
        place_id = "the_place"
        place = Place(id=place_id)
        expected: Mapping[str, Any] = {
            "@context": {
                "names": "https://schema.org/name",
                "enclosers": "https://schema.org/containedInPlace",
                "enclosees": "https://schema.org/containsPlace",
                "events": "https://schema.org/event",
            },
            "@id": "https://example.com/place/the_place/index.json",
            "@type": "https://schema.org/Place",
            "id": place_id,
            "names": [],
            "enclosers": [],
            "enclosees": [],
            "events": [],
            "notes": [],
            "links": [],
            "privacy": False,
            "fileReferences": [],
        }
        actual = await assert_dumps_linked_data(place)
        assert actual == expected

    async def test_dump_linked_data__should_dump_full(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        place_id = "the_place"
        name = "The Place"
        place_name = PlaceName(name)
        latitude = 12.345
        longitude = -54.321
        coordinates = Point(latitude, longitude)
        link = Link("https://example.com/the-place")
        link.label = "The Place Online"
        place = Place(
            id=place_id,
            names=[place_name],
            events=[
                Event(
                    id="E1",
                    event_type=Birth(),
                )
            ],
            links=[link],
        )
        place.coordinates = coordinates
        encloser = Enclosure(enclosee=place, encloser=Place(id="the_enclosing_place"))
        enclosee = Enclosure(enclosee=Place(id="the_enclosed_place"), encloser=place)
        expected: Mapping[str, Any] = {
            "@context": {
                "names": "https://schema.org/name",
                "enclosers": "https://schema.org/containedInPlace",
                "enclosees": "https://schema.org/containsPlace",
                "events": "https://schema.org/event",
                "coordinates": "https://schema.org/geo",
            },
            "@id": "https://example.com/place/the_place/index.json",
            "@type": "https://schema.org/Place",
            "id": place_id,
            "names": [
                {
                    "id": place_name.id,
                    "name": {DEFAULT_LOCALE_TAG: name},
                }
            ],
            "events": [
                "/event/E1/index.json",
            ],
            "notes": [],
            "links": [
                {
                    "@context": {"description": "https://schema.org/description"},
                    "id": link.id,
                    "url": {
                        to_language_tag(
                            DEFAULT_LOCALE
                        ): "https://example.com/the-place",
                    },
                    "label": {
                        DEFAULT_LOCALE_TAG: "The Place Online",
                    },
                    "owner": "/place/the_place/index.json",
                    "privacy": False,
                },
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
            "enclosees": [
                {
                    "id": enclosee.id,
                    "enclosee": "/place/the_enclosed_place/index.json",
                    "encloser": "/place/the_place/index.json",
                    "citations": [],
                }
            ],
            "enclosers": [
                {
                    "id": encloser.id,
                    "enclosee": "/place/the_place/index.json",
                    "encloser": "/place/the_enclosing_place/index.json",
                    "citations": [],
                }
            ],
            "privacy": False,
            "fileReferences": [],
        }
        actual = await assert_dumps_linked_data(place)
        assert actual == expected
