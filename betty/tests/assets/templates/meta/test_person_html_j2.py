from betty.ancestry import Person, Presence, Event, PersonName, Source, Citation, Birth, Subject, Death
from betty.asyncio import sync
from betty.locale import Date
from betty.tests import TemplateTestCase


class Test(TemplateTestCase):
    template_file = 'meta/person.html.j2'

    @sync
    async def test_without_meta(self):
        person = Person('P0')
        expected = '<div class="meta"></div>'
        async with self._render(data={
            'person': person,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_private(self):
        person = Person('P0')
        person.private = True
        expected = '<div class="meta"><p>This person\'s details are unavailable to protect their privacy.</p></div>'
        async with self._render(data={
            'person': person,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_one_alternative_name(self):
        person = Person('P0')
        person.names.append(PersonName('Jane', 'Dough'))
        name = PersonName('Janet', 'Doughnut')
        name.citations.append(Citation(Source('The Source')))
        person.names.append(name)
        expected = '<div class="meta"><span class="aka">Also known as <span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Janet</span> <span property="foaf:familyName">Doughnut</span></span><a href="#reference-1" class="citation">[1]</a></span></div>'
        async with self._render(data={
            'person': person,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_multiple_alternative_names(self):
        person = Person('P0')
        person.names.append(PersonName('Jane', 'Dough'))
        person.names.append(PersonName('Janet', 'Doughnut'))
        person.names.append(PersonName('Janetar', 'Of Doughnuton'))
        expected = '<div class="meta"><span class="aka">Also known as <span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Janet</span> <span property="foaf:familyName">Doughnut</span></span>, <span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Janetar</span> <span property="foaf:familyName">Of Doughnuton</span></span></span></div>'
        async with self._render(data={
            'person': person,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_start(self):
        person = Person('P0')
        Presence(person, Subject(), Event(Birth(), Date(1970)))
        expected = '<div class="meta"><dl><dt>Birth</dt><dd>1970</dd></dl></div>'
        async with self._render(data={
            'person': person,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_end(self):
        person = Person('P0')
        Presence(person, Subject(), Event(Death(), Date(1970)))
        expected = '<div class="meta"><dl><dt>Death</dt><dd>1970</dd></dl></div>'
        async with self._render(data={
            'person': person,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_embedded(self):
        person = Person('P0')
        Presence(person, Subject(), Event(Birth(), Date(1970)))
        person.names.append(PersonName('Jane', 'Dough'))
        name = PersonName('Janet', 'Doughnut')
        name.citations.append(Citation(Source('The Source')))
        person.names.append(name)
        expected = '<div class="meta"><span class="aka">Also known as <span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Janet</span> <span property="foaf:familyName">Doughnut</span></span></span><dl><dt>Birth</dt><dd>1970</dd></dl></div>'
        async with self._render(data={
            'person': person,
            'embedded': True,
        }) as (actual, _):
            self.assertEqual(expected, actual)
