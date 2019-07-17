from os import makedirs
from os.path import join, exists
from tempfile import TemporaryDirectory
from unittest import TestCase

import html5lib
from rdflib import Graph

from betty.ancestry import Person, Event, Place, Reference
from betty.config import Configuration
from betty.render import render
from betty.site import Site


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

        reference1 = Reference('REFERENCE1', 'A Little Birdie')

        places = [place1]
        cls.site.ancestry.places.update({place.id: place for place in places})
        events = [event1]
        cls.site.ancestry.events.update({event.id: event for event in events})
        people = [person1]
        cls.site.ancestry.people.update(
            {person.id: person for person in people})
        references = [reference1]
        cls.site.ancestry.references.update({reference.id: reference for reference in references})

        render(cls.site)

    @classmethod
    def tearDownClass(cls):
        cls._outputDirectory.cleanup()

    def assert_page(self, path: str):
        abspath = join(self.site.configuration.output_directory_path,
                       path.lstrip('/'), 'index.html')
        self.assertTrue(exists(abspath), '%s does not exist' % abspath)
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
        rdf = self._rdf(person)
        print(list(rdf))

    def _rdf(self, person: Person) -> Graph:
        from pyRdfa import pyRdfa
        abspath = join(self.site.configuration.output_directory_path,
                       ('/person/%s' % person.id).lstrip('/'), 'index.html')
        return pyRdfa().graph_from_source(abspath)

    def test_events(self):
        self.assert_page('/event/')

    def test_event(self):
        event = self.site.ancestry.events['EVENT1']
        self.assert_page('/event/%s' % event.id)

    def test_references(self):
        self.assert_page('/reference/')

    def test_reference(self):
        reference = self.site.ancestry.references['REFERENCE1']
        self.assert_page('/reference/%s' % reference.id)

    def test_resource_override(self):
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as resources_directory_path:
                makedirs(join(resources_directory_path, 'public'))
                with open(join(resources_directory_path, 'public', 'index.html.j2'), 'w') as f:
                    f.write('{% block content %}Betty was here{% endblock %}')
                configuration = Configuration(output_directory_path, 'https://ancestry.example.com')
                configuration.resources_directory_path = resources_directory_path
                site = Site(configuration)
                render(site)
                with open(join(output_directory_path, 'index.html')) as f:
                    self.assertIn('Betty was here', f.read())
