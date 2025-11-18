import pytest

from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.app import App
from betty.model import Entity
from betty.project import Project
from betty.project.extension.trees import Trees
from betty.project.extension.trees.content_provider import Tree
from betty.resource import new_context


class TestTree:
    async def test_provide__without_supported_entity(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(Trees)
            async with project:
                sut = await Tree.new_for_project(project)
                assert await sut.provide(resource=new_context()) is None

    @pytest.mark.parametrize(
        "resource",
        [
            Event(),
            Place(),
        ],
    )
    async def test_provide__without_trees(
        self, resource: Entity, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(Trees)
            async with project:
                project.ancestry.add(resource)
                sut = await Tree.new_for_project(project)
                assert (
                    await sut.provide(
                        resource=await project.new_resource_context(resource)
                    )
                    is None
                )

    async def test_provide__with_person_with_relationships(
        self, temporary_app: App
    ) -> None:
        person = Person()
        Person(parents=[person])
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(Trees)
            async with project:
                project.ancestry.add(person)
                sut = await Tree.new_for_project(project)
                resource = await project.new_resource_context(person)
                actual = await sut.provide(resource=resource)
        assert actual is not None
        assert person.public_id in actual
        assert "webpack_js_entry_points" in resource
        assert "trees" in resource["webpack_js_entry_points"]  # type: ignore[typeddict-item]
