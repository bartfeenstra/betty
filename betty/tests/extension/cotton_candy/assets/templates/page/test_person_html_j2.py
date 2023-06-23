from betty.extension import CottonCandy
from betty.model.ancestry import Person, PersonName
from betty.tests import TemplateTestCase


class TestDescendantNames(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = 'entity/page--person.html.j2'

    def test_without_enclosing_places(self) -> None:
        person = Person('P0')
        partner_one = Person('P1')
        child_one = Person('P1C1')
        child_one.parents.append(person)
        child_one.parents.append(partner_one)
        PersonName(child_one, None, 'FamilyOneAssociationName')
        partner_two = Person('P2')
        child_two = Person('P2C2')
        child_two.parents.append(person)
        child_two.parents.append(partner_two)
        PersonName(child_two, None, 'FamilyTwoAssociationName')
        with self._render(data={
            'page_resource': person,
            'entity_type': Person,
            'entity': person,
        }) as (actual, _):
            assert 'Descendant names include FamilyOneAssociationName.' in actual
            assert 'Descendant names include FamilyTwoAssociationName.' in actual
