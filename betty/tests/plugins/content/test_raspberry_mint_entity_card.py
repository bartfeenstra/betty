from betty.document import Document
from betty.entity.reference import EntityReference
from betty.plugins.content.raspberry_mint_entity_card import EntityCard
from betty.plugins.entity.person import Person
from betty.test_utils.conftest import IsolatedProjectFactory


class TestEntityCard:
    async def test_build_template(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(supported_plugins=[EntityCard]) as project:
            entity = Person(id="my-first-entity")
            project.ancestry.add(entity)
            sut = await EntityCard.new(
                project, EntityReference(entity.plugin(), entity.id)
            )

            provided_content = await sut.build(document=Document())
        assert provided_content is not None
        assert entity.public_id in provided_content
