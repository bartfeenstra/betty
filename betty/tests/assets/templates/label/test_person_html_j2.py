from betty.ancestry import Person, PersonName
from betty.asyncio import sync
from betty.tests import TemplateTestCase


class Test(TemplateTestCase):
    template_file = 'label/person.html.j2'

    @sync
    async def test_with_name(self):
        person = Person('P0')
        person.names.append(PersonName('Jane', 'Dough'))
        expected = '<a href="/person/P0/index.html"><span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span></a>'
        async with self._render(data={
            'person': person,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_without_name(self):
        person = Person('P0')
        expected = '<a href="/person/P0/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
        async with self._render(data={
            'person': person,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_embedded(self):
        person = Person('P0')
        expected = '<span class="nn" title="This person\'s name is unknown.">n.n.</span>'
        async with self._render(data={
            'person': person,
            'embedded': True,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_person_is_context(self):
        person = Person('P0')
        expected = '<span class="nn" title="This person\'s name is unknown.">n.n.</span>'
        async with self._render(data={
            'person': person,
            'person_context': person,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_private(self):
        person = Person('P0')
        person.private = True
        expected = '<a href="/person/P0/index.html"><span class="private" title="This person\'s details are unavailable to protect their privacy.">private</span></a>'
        async with self._render(data={
            'person': person,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_resource(self):
        person = Person('P0')
        person.names.append(PersonName('Jane', 'Dough'))
        expected = '<a href="/person/P0/index.html"><span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span></a>'
        async with self._render(data={
            'resource': person,
        }) as (actual, _):
            self.assertEqual(expected, actual)
