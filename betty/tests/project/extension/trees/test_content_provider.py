import pytest
from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.app import App
from betty.content_provider import ContentProvider
from betty.document import Document
from betty.model import Entity
from betty.project import Project
from betty.project.extension.trees import Trees
from betty.project.extension.trees.content_provider import Tree
from betty.test_utils.content_provider import ContentProviderTestBase


class TestTree(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return Tree(jinja2_environment=await project.jinja2_environment)

    async def test_provide__without_supported_entity(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(Trees)
            async with project:
                sut = await Tree.new_for_project(project)
                assert await sut.provide(document=Document()) is None

    @pytest.mark.parametrize(
        "resource",
        [
            Event(),
            Place(),
        ],
    )
    async def test_provide__without_trees(
        self, resource: Entity, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(Trees)
            async with project:
                project.ancestry.add(resource)
                sut = await Tree.new_for_project(project)
                assert (
                    await sut.provide(document=await project.new_document(resource))
                    is None
                )

    async def test_provide__with_person_with_relationships(
        self, isolated_app: App
    ) -> None:
        person = Person()
        Person(parents=[person])
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(Trees)
            async with project:
                project.ancestry.add(person)
                sut = await Tree.new_for_project(project)
                document = await project.new_document(person)
                actual = await sut.provide(document=document)
        assert actual is not None
        assert person.public_id in actual
        assert "webpack_js_entry_points" in document
        assert "trees" in document["webpack_js_entry_points"]  # type: ignore[operator]
