from betty.app import App
from betty.document import Document
from betty.plugins.content.raspberry_mint_external_links import ExternalLinks
from betty.plugins.entity.link import Link
from betty.plugins.entity.person import Person
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.project import Project


class TestExternalLinks:
    async def test_build_template__without_has_links(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await ExternalLinks.new(project)
                provided_content = await sut.build(document=Document(object()))
        assert provided_content is None

    async def test_build_template__with_has_links_without_links(
        self, isolated_app: App
    ) -> None:
        resource = Person()
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await ExternalLinks.new(project)
                assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_has_links_with_links(
        self, isolated_app: App
    ) -> None:
        url = "betty:///my-first-page"
        resource = Person(links=[Link(url)])
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await ExternalLinks.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert url in actual
