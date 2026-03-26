import pytest

from betty.app import App
from betty.document import Document
from betty.plugins.content.raspberry_mint_citations import Citations
from betty.plugins.entity.citation import Citation
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.plugins.entity.source import Source
from betty.project import Project
from betty.test_utils.ancestry.has_citations import DummyHasCitations


class TestCitations:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
            DummyHasCitations(),
        ],
    )
    async def test_build_template__without_citations(
        self, resource: object, isolated_app: App
    ) -> None:
        async with (
            Project.new_isolated(isolated_app, support_plugins=[Citations]) as project,
            project,
        ):
            sut = await project.factory.new(Citations)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_citation(self, isolated_app: App) -> None:
        citation = Citation(source=Source())
        resource = DummyHasCitations(citations=[citation])
        async with (
            Project.new_isolated(isolated_app, support_plugins=[Citations]) as project,
            project,
        ):
            sut = await project.factory.new(Citations)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert 'href="#reference-1"' in actual
