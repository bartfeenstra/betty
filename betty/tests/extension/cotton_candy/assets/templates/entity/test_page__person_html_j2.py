from pathlib import Path

from betty.ancestry import (
    Event,
    Presence,
    FileReference,
)
from betty.ancestry.person_name import PersonName
from betty.ancestry.event_type.event_types import Birth
from betty.ancestry.file import File
from betty.ancestry.person import Person
from betty.ancestry.presence_role.presence_roles import Subject
from betty.date import Date
from betty.extension.cotton_candy import CottonCandy
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.test_utils.assets.templates import TemplateTestBase


class TestTemplate(TemplateTestBase):
    extensions = {CottonCandy}
    template_file = "entity/page--person.html.j2"

    async def test_descendant_names(self) -> None:
        person = Person(id="P0")
        partner_one = Person(id="P1")
        child_one = Person(id="P1C1")
        child_one.parents.add(person)
        child_one.parents.add(partner_one)
        PersonName(
            person=child_one,
            affiliation="FamilyOneAssociationName",
        )
        partner_two = Person(id="P2")
        child_two = Person(id="P2C2")
        child_two.parents.add(person)
        child_two.parents.add(partner_two)
        PersonName(
            person=child_two,
            affiliation="FamilyTwoAssociationName",
        )
        async with self._render(
            data={
                "page_resource": person,
                "entity_type": Person,
                "entity": person,
            },
        ) as (actual, _):
            assert "Descendant names include FamilyOneAssociationName." in actual
            assert "Descendant names include FamilyTwoAssociationName." in actual

    async def test_privacy(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file"
        file_path.touch()

        person = Person()
        public_name_individual = "person public individual"
        public_name_affiliation = "person public affiliation"
        PersonName(
            person=person,
            individual=public_name_individual,
            affiliation=public_name_affiliation,
        )
        private_name_individual = "person private individual"
        private_name_affiliation = "person private affiliation"
        PersonName(
            person=person,
            individual=private_name_individual,
            affiliation=private_name_affiliation,
            private=True,
        )
        public_parent = Person()
        public_parent_public_name_individual = "public parent public individual"
        public_parent_public_name_affiliation = "public parent public affiliation"
        PersonName(
            person=public_parent,
            individual=public_parent_public_name_individual,
            affiliation=public_parent_public_name_affiliation,
        )
        public_parent_private_name_individual = "public parent private individual"
        public_parent_private_name_affiliation = "public parent private  affiliation"
        PersonName(
            person=public_parent,
            individual=public_parent_private_name_individual,
            affiliation=public_parent_private_name_affiliation,
            private=True,
        )
        private_parent = Person(private=True)
        private_parent_public_name_individual = "private parent public individual"
        private_parent_public_name_affiliation = "private parent public affiliation"
        PersonName(
            person=private_parent,
            individual=private_parent_public_name_individual,
            affiliation=private_parent_public_name_affiliation,
        )
        private_parent_private_name_individual = "private parent private individual"
        private_parent_private_name_affiliation = "private parent private affiliation"
        PersonName(
            person=private_parent,
            individual=private_parent_private_name_individual,
            affiliation=private_parent_private_name_affiliation,
            private=True,
        )
        public_partner = Person()
        public_partner_public_name_individual = "public partner public individual"
        public_partner_public_name_affiliation = "public partner public affiliation"
        PersonName(
            person=public_partner,
            individual=public_partner_public_name_individual,
            affiliation=public_partner_public_name_affiliation,
        )
        public_partner_private_name_individual = "public partner private individual"
        public_partner_private_name_affiliation = "public partner private  affiliation"
        PersonName(
            person=public_partner,
            individual=public_partner_private_name_individual,
            affiliation=public_partner_private_name_affiliation,
            private=True,
        )
        private_partner = Person(private=True)
        private_partner_public_name_individual = "private partner public individual"
        private_partner_public_name_affiliation = "private partner public affiliation"
        PersonName(
            person=private_partner,
            individual=private_partner_public_name_individual,
            affiliation=private_partner_public_name_affiliation,
        )
        private_partner_private_name_individual = "private partner private individual"
        private_partner_private_name_affiliation = "private partner private affiliation"
        PersonName(
            person=private_partner,
            individual=private_partner_private_name_individual,
            affiliation=private_partner_private_name_affiliation,
            private=True,
        )
        person.parents = [public_parent, private_parent]
        public_child = Person()
        public_child_public_name_individual = "public child public individual"
        public_child_public_name_affiliation = "public child public affiliation"
        PersonName(
            person=public_child,
            individual=public_child_public_name_individual,
            affiliation=public_child_public_name_affiliation,
        )
        public_child_private_name_individual = "public child private individual"
        public_child_private_name_affiliation = "public child private  affiliation"
        PersonName(
            person=public_child,
            individual=public_child_private_name_individual,
            affiliation=public_child_private_name_affiliation,
            private=True,
        )
        public_child.parents = [person, public_partner, private_partner]
        private_child = Person(private=True)
        private_child_public_name_individual = "private child public individual"
        private_child_public_name_affiliation = "private child public affiliation"
        PersonName(
            person=private_child,
            individual=private_child_public_name_individual,
            affiliation=private_child_public_name_affiliation,
        )
        private_child_private_name_individual = "private child private individual"
        private_child_private_name_affiliation = "private child private affiliation"
        PersonName(
            person=private_child,
            individual=private_child_private_name_individual,
            affiliation=private_child_private_name_affiliation,
        )
        private_child.parents = [person, public_partner, private_partner]
        public_file = File(
            path=file_path,
            description="public file description",
        )
        private_file = File(
            path=file_path,
            private=True,
            description="private file description",
        )
        FileReference(person, public_file)
        FileReference(person, private_file)
        public_event_public_presence = Event(
            id="EVENT1",
            event_type=Birth(),
            date=Date(1970, 1, 1),
            description="public event public presence",
        )
        public_event_private_presence = Event(
            id="EVENT2",
            event_type=Birth(),
            date=Date(1970, 1, 1),
            description="public event private presence",
        )
        private_event_public_presence = Event(
            id="EVENT3",
            event_type=Birth(),
            date=Date(1970, 1, 1),
            private=True,
            description="private event public presence",
        )
        private_event_private_presence = Event(
            id="EVENT4",
            event_type=Birth(),
            date=Date(1970, 1, 1),
            private=True,
            description="private event private presence",
        )
        Presence(person, Subject(), public_event_public_presence)
        Presence(person, Subject(), private_event_public_presence)
        async with self._render(
            data={
                "page_resource": person,
                "entity_type": Person,
                "entity": person,
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
            assert public_file.description
            assert public_file.description.localize(DEFAULT_LOCALIZER) in actual
            assert public_event_public_presence.description
            assert (
                public_event_public_presence.description.localize(DEFAULT_LOCALIZER)
                in actual
            )

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
            assert private_file.description
            assert private_file.description.localize(DEFAULT_LOCALIZER) not in actual
            assert public_event_private_presence.description
            assert (
                public_event_private_presence.description.localize(DEFAULT_LOCALIZER)
                not in actual
            )
            assert private_event_public_presence.description
            assert (
                private_event_public_presence.description.localize(DEFAULT_LOCALIZER)
                not in actual
            )
            assert private_event_private_presence.description
            assert (
                private_event_private_presence.description.localize(DEFAULT_LOCALIZER)
                not in actual
            )
