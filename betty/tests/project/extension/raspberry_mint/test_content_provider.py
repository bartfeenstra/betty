from betty.ancestry.person import Person
from betty.app import App
from betty.locale import DEFAULT_LOCALE
from betty.model.config import EntityReference
from betty.project import Project
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.raspberry_mint.content_provider import FeaturedEntities


class TestFeaturedEntities:
    async def test_provide__without_entities(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            async with project:
                sut = await FeaturedEntities.new_for_project(project)
                assert (
                    await sut.provide(locale=DEFAULT_LOCALE, page_resource=None) == ""
                )

    async def test_provide__with_entities(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(RaspberryMint)
            entity = Person(id="my-first-entity")
            project.ancestry.add(entity)
            async with project:
                sut = await FeaturedEntities.new_for_project(project)
                sut.configuration.append(EntityReference(entity.plugin, entity.id))
                content = await sut.provide(locale=DEFAULT_LOCALE, page_resource=None)
                assert entity.public_id in content
