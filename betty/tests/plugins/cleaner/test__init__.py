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

        onymous_event = Event('E0', Event.Type.BIRTH)
        onymous_event.people.add(Person('P0'))
        ancestry.events[onymous_event.id] = onymous_event

        anonymous_event = Event('E1', Event.Type.BIRTH)
        ancestry.events[anonymous_event.id] = anonymous_event

        onymous_place = Place('P0', 'Amsterdam')
        onymous_place.events.add(onymous_event)
        ancestry.places[onymous_place.id] = onymous_place

        anonymous_place = Place('P1', 'Almelo')
        ancestry.places[anonymous_place.id] = anonymous_place

        anonymous_place_encloses_onymous_places = Place('P3', 'Netherlands')
        anonymous_place_encloses_onymous_places.encloses.add(onymous_place)
        anonymous_place_encloses_onymous_places.encloses.add(anonymous_place)
        ancestry.places[anonymous_place_encloses_onymous_places.id] = anonymous_place_encloses_onymous_places

        clean(ancestry)

        self.assertDictEqual({
            onymous_event.id: onymous_event,
        }, ancestry.events)
        self.assertDictEqual({
            onymous_place.id: onymous_place,
            anonymous_place_encloses_onymous_places.id: anonymous_place_encloses_onymous_places,
        }, ancestry.places)
