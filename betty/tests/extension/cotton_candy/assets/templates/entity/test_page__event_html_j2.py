from pathlib import Path

import pytest

from betty.app import App
from betty.extension import CottonCandy
from betty.locale import DEFAULT_LOCALIZER, Str
from betty.model.ancestry import (
    Event,
    File,
    Place,
    PlaceName,
    Person,
    Presence,
    Subject,
    Citation,
    Source,
)
from betty.model.event_type import UnknownEventType
from betty.tests import TemplateTester


class TestTemplate:
    @pytest.fixture
    def template_tester(self, new_temporary_app: App) -> TemplateTester:
        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        return TemplateTester(
            new_temporary_app, template_file="entity/page--event.html.j2"
        )

    async def test_privacy(
        self, template_tester: TemplateTester, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "file"
        file_path.touch()

        event = Event(event_type=UnknownEventType)

        public_file = File(
            path=file_path,
            description="public file description",
        )
        public_file.entities.add(event)

        private_file = File(
            path=file_path,
            private=True,
            description="private file description",
        )
        private_file.entities.add(event)

        place_name = PlaceName(name="place name")
        place = Place(names=[place_name])
        place.events.add(event)

        public_person_for_presence = Person()
        private_person_for_presence = Person(private=True)
        Presence(public_person_for_presence, Subject(), event)
        Presence(private_person_for_presence, Subject(), event)

        source = Source()

        public_citation = Citation(
            source=source,
            location=Str.plain("public citation location"),
        )
        public_citation.facts.add(event)

        private_citation = Citation(
            source=source,
            private=True,
            location=Str.plain("private citation location"),
        )
        private_citation.facts.add(event)

        async with template_tester.render(
            data={
                "page_resource": event,
                "entity_type": Event,
                "entity": event,
            },
        ) as actual:
            assert public_file.description is not None
            assert public_file.description in actual
            assert place_name.name in actual
            assert (
                public_person_for_presence.label.localize(DEFAULT_LOCALIZER) in actual
            )
            assert public_citation.location is not None
            assert public_citation.location.localize(DEFAULT_LOCALIZER) in actual

            assert private_file.description is not None
            assert private_file.description not in actual
            assert (
                private_person_for_presence.label.localize(DEFAULT_LOCALIZER)
                not in actual
            )
            assert private_citation.location is not None
            assert private_citation.location.localize(DEFAULT_LOCALIZER) not in actual
