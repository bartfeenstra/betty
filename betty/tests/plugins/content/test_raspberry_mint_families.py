import pytest

from betty.document import Document
from betty.plugins.content.raspberry_mint_families import Families
from betty.plugins.entity.event import Event
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.test_utils.conftest import IsolatedProjectFactory


class TestFamilies:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Place(),
            Event(),
        ],
    )
    async def test_build_template__without_person(
        self, resource: object, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[Families]) as project:
            sut = await Families.new(project)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_person(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        parent = Person(id="parent")
        resource = Person(id="resource", parents=[parent])
        child = Person(id="child", parents=[resource])
        async with isolated_project_factory(supported_plugins=[Families]) as project:
            project.ancestry.add(resource)
            sut = await Families.new(project)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert parent.public_id in actual
        assert child.public_id in actual
