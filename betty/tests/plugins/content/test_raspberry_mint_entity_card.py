from betty.app import App
from betty.document import Document
from betty.model.reference import EntityReference
from betty.plugins.content.raspberry_mint_entity_card import EntityCard
from betty.plugins.entity.person import Person
from betty.project import Project


class TestEntityCard:
    async def test_build_template(self, isolated_app: App) -> None:
        async with (
            Project.new_isolated(isolated_app, support_plugins=[EntityCard]) as project,
            project,
        ):
            entity = Person(id="my-first-entity")
            project.ancestry.add(entity)
            sut = await EntityCard.new(
                project, EntityReference(entity.plugin(), entity.id)
            )

            provided_content = await sut.build(document=Document())
        assert provided_content is not None
        assert entity.public_id in provided_content
