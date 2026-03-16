from collections.abc import Iterator, Set
from typing import cast

import pytest
from geopy import Point

from betty.app import App
from betty.document import Document
from betty.model import Entity
from betty.plugins.content.map import Map
from betty.plugins.entity.event import Event
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.plugins.entity.presence import Presence
from betty.plugins.extension.maps import Maps
from betty.plugins.role import Subject
from betty.project import Project


class TestMap:
    async def test_build_template__without_supported_entity(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Maps)
            async with project:
                sut = await Map.new(project)
                assert await sut.build(document=Document()) is None

    @pytest.mark.parametrize(
        "has_associated_places",
        [
            Event(),
            Person(),
            Place(),
        ],
    )
    async def test_build_template__with_entity_without_places(
        self, has_associated_places: Entity, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Maps)
            async with project:
                project.ancestry.add(has_associated_places)
                sut = await Map.new(project)
                assert (
                    await sut.build(
                        document=await project.new_document(has_associated_places)
                    )
                    is None
                )

    @staticmethod
    def _has_map_entities_params() -> Iterator[tuple[Entity, Place]]:
        event_place = Place(coordinates=Point(52.37277778, 4.89361111))
        yield Event(place=event_place), event_place

        person = Person()
        person_event_place = Place(coordinates=Point(52.37277778, 4.89361111))
        person_event = Event(place=person_event_place)
        Presence(person, Subject(), person_event), person_event_place
        yield person, person_event_place

        place = Place(coordinates=Point(52.37277778, 4.89361111))
        yield place, place

    @pytest.fixture(params=_has_map_entities_params())
    def has_map_entities(self, request: pytest.FixtureRequest) -> tuple[Entity, Place]:
        return cast(tuple[Entity, Place], request.param)

    async def test_build_template__with_entity_with_places(
        self, has_map_entities: tuple[Entity, Place], isolated_app: App
    ) -> None:
        has_associated_places, place = has_map_entities
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Maps)
            async with project:
                project.ancestry.add(has_associated_places)
                sut = await Map.new(project)
                document = await project.new_document(has_associated_places)
                actual = await sut.build(document=document)
        assert actual is not None
        assert place.public_id in actual
        assert "webpack_js_entry_points" in document
        assert isinstance(document["webpack_js_entry_points"], Set)
        assert "maps" in document["webpack_js_entry_points"]
