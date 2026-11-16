from betty.content_builders.raspberry_mint_see_also import SeeAlso
from betty.document import Document
from betty.entities.link import Link
from betty.entities.person import Person
from betty.test_utils.conftest import NewIsolatedProject


class TestSeeAlso:
    async def test_build_template__without_has_links(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with (
            new_isolated_project(supported_plugins=[SeeAlso]) as project,
            project,
        ):
            sut = await SeeAlso.new(project)
            provided_content = await sut.build(document=Document(object()))
        assert provided_content is None

    async def test_build_template__with_has_links_without_links(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        resource = Person()
        async with (
            new_isolated_project(supported_plugins=[SeeAlso]) as project,
            project,
        ):
            sut = await SeeAlso.new(project)
            assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_has_links_with_links(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        url = "betty:///my-first-page"
        resource = Person(links=[Link(url)])
        async with (
            new_isolated_project(supported_plugins=[SeeAlso]) as project,
            project,
        ):
            sut = await SeeAlso.new(project)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert url in actual
