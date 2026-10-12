import pytest

from betty.content_builders.raspberry_mint_presences import (
    Presences,
    PresencesData,
)
from betty.document import Document
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entities.presence import Presence
from betty.roles.subject import Subject
from betty.roles.witness import Witness
from betty.test_utils.conftest import NewIsolatedProject
from betty.test_utils.data import DataTestBase


class TestPresencesData(DataTestBase[PresencesData]):
    sut_cls = PresencesData

    def test_include(self) -> None:
        include = ["foo"]
        sut = PresencesData(include=include)
        assert sut.include is not None
        assert list(sut.include) == include

    def test_exclude(self) -> None:
        exclude = ["foo"]
        sut = PresencesData(exclude=exclude)
        assert sut.exclude is not None
        assert list(sut.exclude) == exclude


class TestPresences:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
            Event(),
        ],
    )
    async def test_build_template__without_presences(
        self, resource: object, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with (
            new_isolated_project(supported_plugins=[Presences]) as project,
            project,
        ):
            sut = Presences(jinja=await project.jinja)
            assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_presences(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        person = Person(id="my-first-person")
        resource = Event()
        Presence(person, Subject(), resource)
        async with (
            new_isolated_project(supported_plugins=[Presences]) as project,
            project,
        ):
            sut = Presences(jinja=await project.jinja)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert person.id in actual

    async def test_build_template__with_presences_with_include(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        person_include = Person(id="my-include-person")
        person_exclude = Person(id="my-exclude-person")
        resource = Event()
        Presence(person_include, Subject(), resource)
        Presence(person_exclude, Witness(), resource)
        async with (
            new_isolated_project(supported_plugins=[Presences]) as project,
            project,
        ):
            sut = Presences(include=[Subject], jinja=await project.jinja)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert person_include.id in actual
        assert person_exclude.id not in actual

    async def test_build_template__with_presences_with_exclude(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        person_include = Person(id="my-include-person")
        person_exclude = Person(id="my-exclude-person")
        resource = Event()
        Presence(person_include, Subject(), resource)
        Presence(person_exclude, Witness(), resource)
        async with (
            new_isolated_project(supported_plugins=[Presences]) as project,
            project,
        ):
            sut = await Presences.new(project, PresencesData(exclude=[Witness]))
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert person_include.id in actual
        assert person_exclude.id not in actual
