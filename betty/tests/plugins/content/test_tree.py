from collections.abc import Set

import pytest

from betty.document import Document
from betty.model import Entity
from betty.plugins.content.tree import Tree
from betty.plugins.entity.event import Event
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.test_utils.conftest import IsolatedProjectFactory


class TestTree:
    async def test_build_template__without_supported_entity(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(support_plugins=[Tree]) as project:
            sut = await Tree.new(project)
            assert await sut.build(document=Document()) is None

    @pytest.mark.parametrize(
        "resource",
        [
            Event(),
            Place(),
        ],
    )
    async def test_build_template__without_trees(
        self, resource: Entity, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(support_plugins=[Tree]) as project:
            project.ancestry.add(resource)
            sut = await Tree.new(project)
            assert (
                await sut.build(document=await project.new_document(resource)) is None
            )

    async def test_build_template__with_person_with_relationships(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        person = Person()
        Person(parents=[person])
        async with isolated_project_factory(support_plugins=[Tree]) as project:
            project.ancestry.add(person)
            sut = await Tree.new(project)
            document = await project.new_document(person)
            actual = await sut.build(document=document)
        assert actual is not None
        assert person.public_id in actual
        assert "webpack_js_entry_points" in document
        assert isinstance(document["webpack_js_entry_points"], Set)
        assert "trees" in document["webpack_js_entry_points"]
