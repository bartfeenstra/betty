from betty.ancestry import Person, PersonName
from betty.asyncio import sync
from betty.tests import TemplateTestCase


class TestDescendantNames(TemplateTestCase):
    template_file = 'page/person.html.j2'

    @sync
    async def test_without_enclosing_places(self):
        person = Person('P0')
        partner_one = Person('P1')
        child_one = Person('P1C1')
        child_one.parents.append(person)
        child_one.parents.append(partner_one)
        child_one.names.append(PersonName(None, 'FamilyOneAssociationName'))
        partner_two = Person('P2')
        child_two = Person('P2C2')
        child_two.parents.append(person)
        child_two.parents.append(partner_two)
        child_two.names.append(PersonName(None, 'FamilyTwoAssociationName'))
        async with self._render(data={
            'page_resource': person,
            'entity_type_name': 'person',
            'person': person,
        }) as (actual, _):
            self.assertIn('Descendant names include FamilyOneAssociationName.', actual)
            self.assertIn('Descendant names include FamilyTwoAssociationName.', actual)
