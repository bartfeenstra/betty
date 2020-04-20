from tempfile import TemporaryDirectory
from unittest import TestCase

from betty.ancestry import Person, Event, IdentifiableEvent, Presence
from betty.config import Configuration
from betty.functools import sync
from betty.site import Site


class Test(TestCase):
    async def _render(self, **data):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                return await site.jinja2_environment.get_template('label/event.html.j2').render_async(**data)

    @sync
    async def test_minimal(self):
        event = Event(Event.Type.BIRTH)
        expected = 'Birth'
        actual = await self._render(event=event)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_identifiable(self):
        event = IdentifiableEvent('E0', Event.Type.BIRTH)
        expected = '<a href="/event/E0/index.html">Birth</a>'
        actual = await self._render(event=event)
        self.assertEqual(expected, actual)

    @sync
    async def test_embedded_with_identifiable(self):
        event = IdentifiableEvent('E0', Event.Type.BIRTH)
        Presence(Person('P0'), Presence.Role.SUBJECT, event)
        expected = 'Birth of <span class="nn" title="This person\'s name is unknown.">n.n.</span>'
        actual = await self._render(event=event, embedded=True)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_description(self):
        event = Event(Event.Type.BIRTH)
        event.description = 'Something happened!'
        expected = 'Birth (Something happened!)'
        actual = await self._render(event=event)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_witnesses(self):
        event = Event(Event.Type.BIRTH)
        Presence(Person('P0'), Presence.Role.WITNESS, event)
        expected = 'Birth'
        actual = await self._render(event=event)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_person_context_as_witness(self):
        event = Event(Event.Type.BIRTH)
        person = Person('P0')
        Presence(person, Presence.Role.WITNESS, event)
        expected = 'Birth (Witness)'
        actual = await self._render(event=event, person_context=person)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_person_context_as_subject(self):
        event = Event(Event.Type.BIRTH)
        person = Person('P0')
        Presence(person, Presence.Role.SUBJECT, event)
        expected = 'Birth'
        actual = await self._render(event=event, person_context=person)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_person_context_and_other_as_subject(self):
        event = Event(Event.Type.MARRIAGE)
        person = Person('P0')
        other_person = Person('P1')
        Presence(person, Presence.Role.SUBJECT, event)
        Presence(other_person, Presence.Role.SUBJECT, event)
        expected = 'Marriage with <a href="/person/P1/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
        actual = await self._render(event=event, person_context=person)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_subjects(self):
        event = Event(Event.Type.BIRTH)
        Presence(Person('P0'), Presence.Role.SUBJECT, event)
        Presence(Person('P1'), Presence.Role.SUBJECT, event)
        expected = 'Birth of <a href="/person/P0/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>, <a href="/person/P1/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
        actual = await self._render(event=event)
        self.assertEqual(expected, actual)

    @sync
    async def test_without_subjects(self):
        event = Event(Event.Type.BIRTH)
        expected = 'Birth'
        actual = await self._render(event=event)
        self.assertEqual(expected, actual)

    @sync
    async def test_with_resource(self):
        event = Event(Event.Type.BIRTH)
        expected = 'Birth'
        actual = await self._render(resource=event)
        self.assertEqual(expected, actual)
