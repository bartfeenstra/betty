from betty.cotton_candy import CottonCandy
from betty.locale import Date
from betty.model.ancestry import Person, Presence, Event, PersonName, Source, Citation, Subject
from betty.model.event_type import Birth, Death
from betty.tests import TemplateTestCase


class Test(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = 'entity/meta--person.html.j2'

    def test_without_meta(self):
        person = Person('P0')
        expected = '<div class="meta person-meta"></div>'
        with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    def test_private(self):
        person = Person('P0')
        person.private = True
        expected = '<div class="meta person-meta"><p>This person\'s details are unavailable to protect their privacy.</p></div>'
        with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    def test_with_one_alternative_name(self):
        person = Person('P0')
        PersonName(person, 'Jane', 'Dough')
        name = PersonName(person, 'Janet', 'Doughnut')
        name.citations.append(Citation(None, Source(None, 'The Source')))
        expected = '<div class="meta person-meta"><span class="aka">Also known as <span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Janet</span> <span property="foaf:familyName">Doughnut</span></span><a href="#reference-1" class="citation">[1]</a></span></div>'
        with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    def test_with_multiple_alternative_names(self):
        person = Person('P0')
        PersonName(person, 'Jane', 'Dough')
        PersonName(person, 'Janet', 'Doughnut')
        PersonName(person, 'Janetar', 'Of Doughnuton')
        expected = '<div class="meta person-meta"><span class="aka">Also known as <span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Janet</span> <span property="foaf:familyName">Doughnut</span></span>, <span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Janetar</span> <span property="foaf:familyName">Of Doughnuton</span></span></span></div>'
        with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    def test_with_start(self):
        person = Person('P0')
        Presence(person, Subject(), Event(None, Birth(), Date(1970)))
        expected = '<div class="meta person-meta"><dl><div><dt>Birth</dt><dd>1970</dd></div></dl></div>'
        with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    def test_with_end(self):
        person = Person('P0')
        Presence(person, Subject(), Event(None, Death(), Date(1970)))
        expected = '<div class="meta person-meta"><dl><div><dt>Death</dt><dd>1970</dd></div></dl></div>'
        with self._render(data={
            'entity': person,
        }) as (actual, _):
            assert expected == actual

    def test_embedded(self):
        person = Person('P0')
        Presence(person, Subject(), Event(None, Birth(), Date(1970)))
        PersonName(person, 'Jane', 'Dough')
        name = PersonName(person, 'Janet', 'Doughnut')
        name.citations.append(Citation(None, Source(None, 'The Source')))
        expected = '<div class="meta person-meta"><span class="aka">Also known as <span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Janet</span> <span property="foaf:familyName">Doughnut</span></span></span><dl><div><dt>Birth</dt><dd>1970</dd></div></dl></div>'
        with self._render(data={
            'entity': person,
            'embedded': True,
        }) as (actual, _):
            assert expected == actual
