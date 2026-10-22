import pytest

from betty.content_builders.raspberry_mint_citations import Citations
from betty.document import Document
from betty.entities.citation import Citation
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entities.source import Source
from betty.test_utils.conftest import NewIsolatedProject
from betty.test_utils.entity.associations.has_citations import DummyHasCitations


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
        self, resource: object, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with (
            new_isolated_project(supported_plugins=[Citations]) as project,
            project,
        ):
            sut = await project.factory.new(Citations)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_citation(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        citation = Citation(source=Source())
        resource = DummyHasCitations(citations=[citation])
        async with (
            new_isolated_project(supported_plugins=[Citations]) as project,
            project,
        ):
            sut = await project.factory.new(Citations)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert 'href="#reference-1"' in actual
