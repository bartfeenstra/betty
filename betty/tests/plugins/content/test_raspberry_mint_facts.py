import pytest

from betty.app import App
from betty.document import Document
from betty.plugins.content.raspberry_mint_facts import Facts
from betty.plugins.entity.citation import Citation
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.plugins.entity.source import Source
from betty.project import Project
from betty.test_utils.ancestry.has_citations import DummyHasCitations


class TestFacts:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
        ],
    )
    async def test_build_template__without_associated_facts(
        self, resource: object, isolated_app: App
    ) -> None:
        async with (
            Project.new_isolated(isolated_app, support_plugins=[Facts]) as project,
            project,
        ):
            sut = await Facts.new(project)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_citation(self, isolated_app: App) -> None:
        resource = Citation(source=Source())
        fact = DummyHasCitations(citations=[resource])
        async with (
            Project.new_isolated(isolated_app, support_plugins=[Facts]) as project,
            project,
        ):
            sut = await Facts.new(project)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert fact.public_id in actual

    async def test_build_template__with_source(self, isolated_app: App) -> None:
        resource = Source()
        citation = Citation(source=resource)
        fact = DummyHasCitations(citations=[citation])
        async with (
            Project.new_isolated(isolated_app, support_plugins=[Facts]) as project,
            project,
        ):
            sut = await Facts.new(project)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert fact.public_id in actual
