from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Ancestry, Person, Event, Place
from betty.config import Configuration
from betty.parse import parse
from betty.plugins.cleaner import Cleaner, clean
from betty.site import Site


class CleanerTest(TestCase):
    def test_post_parse(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Cleaner] = {}
            with Site(configuration) as site:
                event = Event('E0', Event.Type.BIRTH)
                site.ancestry.events[event.id] = event
                parse(site)
                self.assertEquals({}, site.ancestry.events)

    def test_clean(self):
        ancestry = Ancestry()
        event_with_person = Event('E0', Event.Type.BIRTH)
        event_with_person.people.add(Person('P0'))
        anonymized_event = Event('E1', Event.Type.BIRTH)
        ancestry.events[event_with_person.id] = event_with_person
        ancestry.events[anonymized_event.id] = anonymized_event
        place_with_event = Place('P0', 'Amsterdam')
        place_with_event.events.add(event_with_person)
        anonymized_place = Place('P1', 'Almelo')
        ancestry.places[place_with_event.id] = place_with_event
        ancestry.places[anonymized_place.id] = anonymized_place
        clean(ancestry)
        self.assertEquals({
            event_with_person.id: event_with_person,
        }, ancestry.events)
        self.assertEquals({
            place_with_event.id: place_with_event,
        }, ancestry.places)
