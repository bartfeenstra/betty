from collections.abc import Iterator, Set
from typing import cast

import pytest
from geopy import Point
from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.presence import Presence
from betty.app import App
from betty.content_provider import ContentProvider
from betty.document import Document
from betty.extension.maps import Maps
from betty.extension.maps.content_provider import Map, MapAttribution
from betty.model import Entity
from betty.presence_role.presence_roles import Subject
from betty.project import Project
from betty.test_utils.content_provider import ContentProviderTestBase


class TestMap(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return Map(jinja2_environment=await project.jinja2_environment)

    async def test_provide__without_supported_entity(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Maps)
            async with project:
                sut = await Map.new_for_services(services=project)
                assert await sut.provide(document=Document()) is None

    @pytest.mark.parametrize(
        "has_associated_places",
        [
            Event(),
            Person(),
            Place(),
        ],
    )
    async def test_provide__with_entity_without_places(
        self, has_associated_places: Entity, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Maps)
            async with project:
                project.ancestry.add(has_associated_places)
                sut = await Map.new_for_services(services=project)
                assert (
                    await sut.provide(
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

    async def test_provide__with_entity_with_places(
        self, has_map_entities: tuple[Entity, Place], isolated_app: App
    ) -> None:
        has_associated_places, place = has_map_entities
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Maps)
            async with project:
                project.ancestry.add(has_associated_places)
                sut = await Map.new_for_services(services=project)
                document = await project.new_document(has_associated_places)
                actual = await sut.provide(document=document)
        assert actual is not None
        assert place.public_id in actual
        assert "webpack_js_entry_points" in document
        assert isinstance(document["webpack_js_entry_points"], Set)
        assert "maps" in document["webpack_js_entry_points"]


class TestMapAttribution(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return MapAttribution(jinja2_environment=await project.jinja2_environment)

    async def test_provide(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Maps)
            async with project:
                sut = await MapAttribution.new_for_services(services=project)
                actual = await sut.provide(document=Document())
        assert actual
