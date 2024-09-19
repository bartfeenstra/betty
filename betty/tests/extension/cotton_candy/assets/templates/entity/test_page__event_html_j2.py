from pathlib import Path

from betty.ancestry import (
    Event,
    File,
    Place,
    Name,
    Person,
    Presence,
    Citation,
    Source,
    FileReference,
)
from betty.ancestry.event_type.event_types import Unknown as UnknownEventType
from betty.ancestry.presence_role.presence_roles import Subject
from betty.extension.cotton_candy import CottonCandy
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.test_utils.assets.templates import TemplateTestBase


class TestTemplate(TemplateTestBase):
    extensions = {CottonCandy}
    template_file = "entity/page--event.html.j2"

    async def test_privacy(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file"
        file_path.touch()

        event = Event(event_type=UnknownEventType())

        public_file = File(
            path=file_path,
            description="public file description",
        )
        FileReference(event, public_file)

        private_file = File(
            path=file_path,
            private=True,
            description="private file description",
        )
        FileReference(event, private_file)

        place_name = Name("place name")
        place = Place(names=[place_name])
        place.events.add(event)

        public_person_for_presence = Person()
        private_person_for_presence = Person(private=True)
        Presence(public_person_for_presence, Subject(), event)
        Presence(private_person_for_presence, Subject(), event)

        source = Source()

        public_citation = Citation(
            source=source,
            location="public citation location",
        )
        public_citation.facts.add(event)

        private_citation = Citation(
            source=source,
            private=True,
            location="private citation location",
        )
        private_citation.facts.add(event)

        async with self._render(
            data={
                "page_resource": event,
                "entity_type": Event,
                "entity": event,
            },
        ) as (actual, _):
            assert public_file.description
            assert public_file.description.localize(DEFAULT_LOCALIZER) in actual
            assert place_name
            assert place_name.localize(DEFAULT_LOCALIZER) in actual
            assert (
                public_person_for_presence.label.localize(DEFAULT_LOCALIZER) in actual
            )
            assert public_citation.location is not None
            assert public_citation.location.localize(DEFAULT_LOCALIZER) in actual

            assert private_file.description
            assert private_file.description.localize(DEFAULT_LOCALIZER) not in actual
            assert (
                private_person_for_presence.label.localize(DEFAULT_LOCALIZER)
                not in actual
            )
            assert private_citation.location is not None
            assert private_citation.location.localize(DEFAULT_LOCALIZER) not in actual
