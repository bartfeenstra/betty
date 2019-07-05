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
            site = Site(configuration)
            event = Event('E0', Event.Type.BIRTH)
            site.ancestry.events[event.id] = event
            parse(site)
            self.assertEquals({}, site.ancestry.events)


class CleanTest(TestCase):
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

        onmyous_place_because_encloses_onmyous_places = Place('P3', 'Netherlands')
        onmyous_place_because_encloses_onmyous_places.encloses.add(onymous_place)
        onmyous_place_because_encloses_onmyous_places.encloses.add(anonymous_place)
        ancestry.places[
            onmyous_place_because_encloses_onmyous_places.id] = onmyous_place_because_encloses_onmyous_places

        clean(ancestry)

        self.assertDictEqual({
            onymous_event.id: onymous_event,
        }, ancestry.events)
        self.assertDictEqual({
            onymous_place.id: onymous_place,
            onmyous_place_because_encloses_onmyous_places.id: onmyous_place_because_encloses_onmyous_places,
        }, ancestry.places)

        self.assertNotIn(anonymous_place, onmyous_place_because_encloses_onmyous_places.encloses)

    def test_clean_should_clean_private_people_without_descendants(self):
        ancestry = Ancestry()

        person = Person('P0')
        person.private = False
        ancestry.people[person.id] = person
        child = Person('P1')
        child.private = True
        ancestry.people[child.id] = child
        grandchild = Person('P2')
        grandchild.private = True
        ancestry.people[grandchild.id] = grandchild
        great_grandchild = Person('P3')
        great_grandchild.private = True
        ancestry.people[great_grandchild.id] = great_grandchild

        clean(ancestry)

        self.assertEquals(1, len(ancestry.people))
