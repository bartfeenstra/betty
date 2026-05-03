import pytest

from betty.document import Document
from betty.plugins.content.raspberry_mint_presences import (
    Presences,
    PresencesData,
)
from betty.plugins.entity.event import Event
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.plugins.entity.presence import Presence
from betty.plugins.role.subject import Subject
from betty.plugins.role.witness import Witness
from betty.test_utils.conftest import IsolatedProjectFactory
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
        self, resource: object, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[Presences]) as project:
            sut = Presences(jinja=await project.jinja)
            assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_presences(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        person = Person(id="P1")
        resource = Event()
        Presence(person, Subject(), resource)
        async with isolated_project_factory(supported_plugins=[Presences]) as project:
            sut = Presences(jinja=await project.jinja)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert person.public_id in actual

    async def test_build_template__with_presences_with_include(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        person_include = Person(id="P1")
        person_exclude = Person(id="P2")
        resource = Event()
        Presence(person_include, Subject(), resource)
        Presence(person_exclude, Witness(), resource)
        async with isolated_project_factory(supported_plugins=[Presences]) as project:
            sut = Presences(include=[Subject], jinja=await project.jinja)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert person_include.public_id in actual
        assert person_exclude.public_id not in actual

    async def test_build_template__with_presences_with_exclude(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        person_include = Person(id="P1")
        person_exclude = Person(id="P2")
        resource = Event()
        Presence(person_include, Subject(), resource)
        Presence(person_exclude, Witness(), resource)
        async with isolated_project_factory(supported_plugins=[Presences]) as project:
            sut = await Presences.new(project, PresencesData(exclude=[Witness]))
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert person_include.public_id in actual
        assert person_exclude.public_id not in actual
