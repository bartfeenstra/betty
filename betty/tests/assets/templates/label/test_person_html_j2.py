from betty.ancestry import Person, PersonName
from betty.functools import sync
from betty.tests.assets.templates import TemplateTestCase


class Test(TemplateTestCase):
    template = 'label/person.html.j2'

    @sync
    async def test_with_name(self):
        person = Person('P0')
        person.names.append(PersonName('Jane', 'Dough'))
        expected = '<a href="/person/P0/index.html"><span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span></a>'
        actual = await self._render(person=person)
        self.assertEqual(expected, actual)

    @sync
    async def test_without_name(self):
        person = Person('P0')
        expected = '<a href="/person/P0/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
        actual = await self._render(person=person)
        self.assertEqual(expected, actual)

    @sync
    async def test_embedded(self):
        person = Person('P0')
        expected = '<span class="nn" title="This person\'s name is unknown.">n.n.</span>'
        actual = await self._render(person=person, embedded=True)
        self.assertEqual(expected, actual)

    @sync
    async def test_person_is_context(self):
        person = Person('P0')
        expected = '<span class="nn" title="This person\'s name is unknown.">n.n.</span>'
        actual = await self._render(person=person, person_context=person)
        self.assertEqual(expected, actual)

    @sync
    async def test_private(self):
        person = Person('P0')
        person.private = True
        expected = '<a href="/person/P0/index.html"><span class="private" title="This person\'s details are unavailable to protect their privacy.">private</span></a>'
        actual = await self._render(person=person)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_resource(self):
        person = Person('P0')
        person.names.append(PersonName('Jane', 'Dough'))
        expected = '<a href="/person/P0/index.html"><span class="person-label" typeof="foaf:Person"><span property="foaf:individualName">Jane</span> <span property="foaf:familyName">Dough</span></span></a>'
        actual = await self._render(resource=person)
        self.assertEqual(expected, actual)
