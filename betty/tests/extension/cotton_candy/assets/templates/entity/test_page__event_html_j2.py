from pathlib import Path

from betty.extension import CottonCandy
from betty.model.ancestry import Event, File, Place, PlaceName, Person, Presence, Subject, Citation, Source
from betty.model.event_type import UnknownEventType
from betty.tests import TemplateTestCase


class TestTemplate(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = 'entity/page--event.html.j2'

    async def test_privacy(self) -> None:
        event = Event(None, UnknownEventType)

        public_file = File(None, Path())
        public_file.description = 'public file description'
        public_file.entities.add(event)

        private_file = File(None, Path())
        private_file.private = True
        private_file.description = 'private file description'
        private_file.entities.add(event)

        place_name = PlaceName('place name')
        place = Place(None, [place_name])
        place.events.add(event)

        public_person_for_presence = Person(None)
        private_person_for_presence = Person(None)
        private_person_for_presence.private = True
        Presence(None, public_person_for_presence, Subject(), event)
        Presence(None, private_person_for_presence, Subject(), event)

        source = Source(None)

        public_citation = Citation(None, source)
        public_citation.location = 'public citation location'
        public_citation.facts.add(event)

        private_citation = Citation(None, source)
        private_citation.private = True
        private_citation.location = 'private citation location'
        private_citation.facts.add(event)

        async with self._render(
            data={
                'page_resource': event,
                'entity_type': Event,
                'entity': event,
            },
        ) as (actual, _):
            assert public_file.description in actual
            assert place_name.name in actual
            assert public_person_for_presence.label in actual
            assert public_citation.location in actual

            assert private_file.description not in actual
            assert private_person_for_presence.label not in actual
            assert private_citation.location not in actual
