import os
from os.path import join
from tempfile import TemporaryDirectory
from unittest import TestCase

import html5lib

from betty.ancestry import Person, Event, Place
from betty.config import Configuration
from betty.render import render, _render_walk, _render_flatten
from betty.site import Site


class RenderFlattenTest(TestCase):
    def test_without_items(self):
        self.assertCountEqual([], _render_flatten([]))

    def test_with_empty_items(self):
        self.assertCountEqual([], _render_flatten([[], [], []]))

    def test_with_non_empty_items(self):
        self.assertCountEqual(['apple', 'banana', 'kiwi'], _render_flatten(
            [['kiwi'], ['apple'], ['banana']]))


class RenderWalkTest(TestCase):
    class Data:
        def __init__(self, children=None):
            self.children = children or []

    def test_without_children(self):
        data = self.Data()
        self.assertCountEqual([], _render_walk(data, 'children'))

    def test_with_children(self):
        child1child1 = self.Data()
        child1 = self.Data([child1child1])
        child2 = self.Data()
        data = self.Data([child1, child2])
        expected = [child1, child2, child1child1]
        self.assertCountEqual(expected, _render_walk(data, 'children'))


class RenderTest(TestCase):
    _outputDirectory = None
    site = None

    @classmethod
    def setUpClass(cls):
        cls._outputDirectory = TemporaryDirectory()
        configuration = Configuration(
            cls._outputDirectory.name, 'https://ancestry.example.com')
        cls.site = Site(configuration)

        place1 = Place('PLACE1', 'one')

        event1 = Event('EVENT1', Event.Type.BIRTH)
        event1.place = place1

        person1 = Person('PERSON1', 'Janet', 'Dough')
        person1.events.add(event1)

        places = [place1]
        cls.site.ancestry.places.update({place.id: place for place in places})
        events = [event1]
        cls.site.ancestry.events.update({event.id: event for event in events})
        people = [person1]
        cls.site.ancestry.people.update(
            {person.id: person for person in people})

        render(cls.site)

    @classmethod
    def tearDownClass(cls):
        cls._outputDirectory.cleanup()

    def assert_page(self, path: str):
        abspath = join(self.site.configuration.output_directory_path,
                       path.lstrip('/'), 'index.html')
        self.assertTrue(os.path.exists(abspath), '%s does not exist' % abspath)
        with open(abspath) as f:
            parser = html5lib.HTMLParser(strict=True)
            parser.parse(f)

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
