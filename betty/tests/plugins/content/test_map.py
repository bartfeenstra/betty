from collections.abc import Iterator, Set
from typing import cast

import pytest
from geopy import Point

from betty.document import Document
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entities.presence import Presence
from betty.entity import Entity
from betty.plugins.content.map import Map
from betty.roles.subject import Subject
from betty.test_utils.conftest import IsolatedProjectFactory


class TestMap:
    async def test_build_template__without_supported_entity(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[Map]) as project:
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
        self,
        has_associated_places: Entity,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with isolated_project_factory(supported_plugins=[Map]) as project:
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
        self,
        has_map_entities: tuple[Entity, Place],
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        has_associated_places, place = has_map_entities
        async with isolated_project_factory(supported_plugins=[Map]) as project:
            project.ancestry.add(has_associated_places)
            sut = await Map.new(project)
            document = await project.new_document(has_associated_places)
            actual = await sut.build(document=document)
        assert actual is not None
        assert place.public_id in actual
        assert "webpack_js_entry_points" in document
        assert isinstance(document["webpack_js_entry_points"], Set)
        assert "maps" in document["webpack_js_entry_points"]
