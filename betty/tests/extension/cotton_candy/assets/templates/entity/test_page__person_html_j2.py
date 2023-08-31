from pathlib import Path

from betty.extension import CottonCandy
from betty.locale import Date
from betty.model.ancestry import Person, PersonName, File, Event, Presence, Subject
from betty.model.event_type import Birth
from betty.tests import TemplateTestCase


class TestTemplate(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = 'entity/page--person.html.j2'

    def test_descendant_names(self) -> None:
        person = Person('P0')
        partner_one = Person('P1')
        child_one = Person('P1C1')
        child_one.parents.add(person)
        child_one.parents.add(partner_one)
        PersonName(None, child_one, None, 'FamilyOneAssociationName')
        partner_two = Person('P2')
        child_two = Person('P2C2')
        child_two.parents.add(person)
        child_two.parents.add(partner_two)
        PersonName(None, child_two, None, 'FamilyTwoAssociationName')
        with self._render(
            data={
                'page_resource': person,
                'entity_type': Person,
                'entity': person,
            },
        ) as (actual, _):
            assert 'Descendant names include FamilyOneAssociationName.' in actual
            assert 'Descendant names include FamilyTwoAssociationName.' in actual

    async def test_privacy(self) -> None:
        person = Person(None)
        public_name_individual = 'person public individual'
        public_name_affiliation = 'person public affiliation'
        PersonName(
            None,
            person,
            public_name_individual,
            public_name_affiliation,
        )
        private_name_individual = 'person private individual'
        private_name_affiliation = 'person private affiliation'
        private_name = PersonName(
            None,
            person,
            private_name_individual,
            private_name_affiliation,
        )
        private_name.private = True
        public_parent = Person(None)
        public_parent_public_name_individual = 'public parent public individual'
        public_parent_public_name_affiliation = 'public parent public affiliation'
        PersonName(
            None,
            public_parent,
            public_parent_public_name_individual,
            public_parent_public_name_affiliation,
        )
        public_parent_private_name_individual = 'public parent private individual'
        public_parent_private_name_affiliation = 'public parent private  affiliation'
        public_parent_private_name = PersonName(
            None,
            public_parent,
            public_parent_private_name_individual,
            public_parent_private_name_affiliation,
        )
        public_parent_private_name.private = True
        private_parent = Person(None)
        private_parent.private = True
        private_parent_public_name_individual = 'private parent public individual'
        private_parent_public_name_affiliation = 'private parent public affiliation'
        PersonName(
            None,
            private_parent,
            private_parent_public_name_individual,
            private_parent_public_name_affiliation,
        )
        private_parent_private_name_individual = 'private parent private individual'
        private_parent_private_name_affiliation = 'private parent private affiliation'
        private_parent_private_name = PersonName(
            None,
            private_parent,
            private_parent_private_name_individual,
            private_parent_private_name_affiliation,
        )
        private_parent_private_name.private = True
        public_partner = Person(None)
        public_partner_public_name_individual = 'public partner public individual'
        public_partner_public_name_affiliation = 'public partner public affiliation'
        PersonName(
            None,
            public_partner,
            public_partner_public_name_individual,
            public_partner_public_name_affiliation,
        )
        public_partner_private_name_individual = 'public partner private individual'
        public_partner_private_name_affiliation = 'public partner private  affiliation'
        public_partner_private_name = PersonName(
            None,
            public_partner,
            public_partner_private_name_individual,
            public_partner_private_name_affiliation,
        )
        public_partner_private_name.private = True
        private_partner = Person(None)
        private_partner.private = True
        private_partner_public_name_individual = 'private partner public individual'
        private_partner_public_name_affiliation = 'private partner public affiliation'
        PersonName(
            None,
            private_partner,
            private_partner_public_name_individual,
            private_partner_public_name_affiliation,
        )
        private_partner_private_name_individual = 'private partner private individual'
        private_partner_private_name_affiliation = 'private partner private affiliation'
        private_partner_private_name = PersonName(
            None,
            private_partner,
            private_partner_private_name_individual,
            private_partner_private_name_affiliation,
        )
        private_partner_private_name.private = True
        person.parents = [public_parent, private_parent]  # type: ignore[assignment]
        public_child = Person(None)
        public_child_public_name_individual = 'public child public individual'
        public_child_public_name_affiliation = 'public child public affiliation'
        PersonName(
            None,
            public_child,
            public_child_public_name_individual,
            public_child_public_name_affiliation,
        )
        public_child_private_name_individual = 'public child private individual'
        public_child_private_name_affiliation = 'public child private  affiliation'
        public_child_private_name = PersonName(
            None,
            public_child,
            public_child_private_name_individual,
            public_child_private_name_affiliation,
        )
        public_child_private_name.private = True
        public_child.parents = [person, public_partner, private_partner]  # type: ignore[assignment]
        private_child = Person(None)
        private_child.private = True
        private_child_public_name_individual = 'private child public individual'
        private_child_public_name_affiliation = 'private child public affiliation'
        PersonName(
            None,
            private_child,
            private_child_public_name_individual,
            private_child_public_name_affiliation,
        )
        private_child_private_name_individual = 'private child private individual'
        private_child_private_name_affiliation = 'private child private affiliation'
        PersonName(
            None,
            private_child,
            private_child_private_name_individual,
            private_child_private_name_affiliation,
        )
        private_child.parents = [person, public_partner, private_partner]  # type: ignore[assignment]
        public_file = File(None, Path())
        public_file.description = 'public file description'
        private_file = File(None, Path())
        private_file.description = 'private file description'
        private_file.private = True
        person.files = [public_file, private_file]  # type: ignore[assignment]
        public_event_public_presence = Event('EVENT1', Birth, Date(1970, 1, 1))
        public_event_public_presence.description = 'public event public presence'
        public_event_private_presence = Event('EVENT2', Birth, Date(1970, 1, 1))
        public_event_private_presence.description = 'public event private presence'
        private_event_public_presence = Event('EVENT3', Birth, Date(1970, 1, 1))
        private_event_public_presence.description = 'private event public presence'
        private_event_public_presence.private = True
        private_event_private_presence = Event('EVENT4', Birth, Date(1970, 1, 1))
        private_event_private_presence.description = 'private event private presence'
        private_event_private_presence.private = True
        Presence(None, person, Subject(), public_event_public_presence)
        Presence(None, person, Subject(), private_event_public_presence)
        with self._render(
            data={
                'page_resource': person,
                'entity_type': Person,
                'entity': person,
            },
        ) as (actual, _):
            assert public_name_individual in actual
            assert public_name_affiliation in actual
            assert public_parent_public_name_individual in actual
            assert public_parent_public_name_affiliation in actual
            assert public_child_public_name_individual in actual
            assert public_child_public_name_affiliation in actual
            assert public_partner_public_name_individual in actual
            assert public_partner_public_name_affiliation in actual
            assert public_file.description in actual
            assert public_event_public_presence.description in actual

            assert private_name_individual not in actual
            assert private_name_affiliation not in actual
            assert public_parent_private_name_individual not in actual
            assert public_parent_private_name_affiliation not in actual
            assert private_parent_public_name_individual not in actual
            assert private_parent_public_name_affiliation not in actual
            assert private_parent_private_name_individual not in actual
            assert private_parent_private_name_affiliation not in actual
            assert public_child_private_name_individual not in actual
            assert public_child_private_name_affiliation not in actual
            assert private_child_public_name_individual not in actual
            assert private_child_public_name_affiliation not in actual
            assert private_child_private_name_individual not in actual
            assert private_child_private_name_affiliation not in actual
            assert public_partner_private_name_individual not in actual
            assert public_partner_private_name_affiliation not in actual
            assert private_partner_public_name_individual not in actual
            assert private_partner_public_name_affiliation not in actual
            assert private_partner_private_name_individual not in actual
            assert private_partner_private_name_affiliation not in actual
            assert private_file.description not in actual
            assert public_event_private_presence.description not in actual
            assert private_event_public_presence.description not in actual
            assert private_event_private_presence.description not in actual
