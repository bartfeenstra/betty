from betty.content_builders.raspberry_mint_see_also import SeeAlso
from betty.document import Document
from betty.entities.link import Link
from betty.entities.person import Person
from betty.test_utils.conftest import IsolatedProjectFactory


class TestSeeAlso:
    async def test_build_template__without_has_links(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[SeeAlso]) as project:
            sut = await SeeAlso.new(project)
            provided_content = await sut.build(document=Document(object()))
        assert provided_content is None

    async def test_build_template__with_has_links_without_links(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        resource = Person()
        async with isolated_project_factory(supported_plugins=[SeeAlso]) as project:
            sut = await SeeAlso.new(project)
            assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_has_links_with_links(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        url = "betty:///my-first-page"
        resource = Person(links=[Link(url)])
        async with isolated_project_factory(supported_plugins=[SeeAlso]) as project:
            sut = await SeeAlso.new(project)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert url in actual
