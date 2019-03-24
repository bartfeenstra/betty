import os
from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Ancestry, Person, Event, Place
from betty.config import Configuration
from betty.render import render
from betty.site import Site


class RenderTest(TestCase):
    _outputDirectory = None
    site = None

    @classmethod
    def setUpClass(cls):
        ancestry = Ancestry()

        place1 = Place('PLACE1')

        event1 = Event('EVENT1', Event.Type.BIRTH)
        event1.place = place1

        person1 = Person('PERSON1', 'Janet', 'Dough')
        person1.events.add(event1)

        places = [place1]
        ancestry.places.update({place.id: place for place in places})
        events = [event1]
        ancestry.events.update({event.id: event for event in events})
        people = [person1]
        ancestry.people.update({person.id: person for person in people})

        cls._outputDirectory = TemporaryDirectory()
        configuration = Configuration(None, cls._outputDirectory.name, 'https://ancestry.example.com')
        cls.site = Site(ancestry, configuration)
        render(cls.site)

    @classmethod
    def tearDownClass(cls):
        cls._outputDirectory.cleanup()

    def assert_page(self, path: str):
        abspath = join(self.site.configuration.output_directory_path, path.lstrip('/'), 'index.html')
        self.assertTrue(os.path.exists(abspath), '%s does not exist' % abspath)

    def test_front_page(self):
        self.assert_page('/')

    def test_places(self):
        self.assert_page('/place/')

    def test_place(self):
        place = self.site.ancestry.places['PLACE1']
        self.assert_page('/place/%s' % place.id)

    def test_people(self):
        self.assert_page('/person/')

    def test_person(self):
        person = self.site.ancestry.people['PERSON1']
        self.assert_page('/person/%s' % person.id)

    def test_events(self):
        self.assert_page('/event/')

    def test_event(self):
        event = self.site.ancestry.events['EVENT1']
        self.assert_page('/event/%s' % event.id)
