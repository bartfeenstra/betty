from betty.ancestry import Person, Event, IdentifiableEvent, Presence, Subject, Witness, Birth, Marriage
from betty.asyncio import sync
from betty.tests import TemplateTestCase


class Test(TemplateTestCase):
    template_file = 'label/event.html.j2'

    @sync
    async def test_minimal(self):
        event = Event(Birth())
        expected = 'Birth'
        async with self._render(data={
            'event': event,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_identifiable(self):
        event = IdentifiableEvent('E0', Birth())
        expected = '<a href="/event/E0/index.html">Birth</a>'
        async with self._render(data={
            'event': event,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_embedded_with_identifiable(self):
        event = IdentifiableEvent('E0', Birth())
        Presence(Person('P0'), Subject(), event)
        expected = 'Birth of <span class="nn" title="This person\'s name is unknown.">n.n.</span>'
        async with self._render(data={
            'event': event,
            'embedded': True,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_description(self):
        event = Event(Birth())
        event.description = 'Something happened!'
        expected = 'Birth (Something happened!)'
        async with self._render(data={
            'event': event,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_witnesses(self):
        event = Event(Birth())
        Presence(Person('P0'), Witness(), event)
        expected = 'Birth'
        async with self._render(data={
            'event': event,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_person_context_as_witness(self):
        event = Event(Birth())
        person = Person('P0')
        Presence(person, Witness(), event)
        expected = 'Birth (Witness)'
        async with self._render(data={
            'event': event,
            'person_context': person,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_person_context_as_subject(self):
        event = Event(Birth())
        person = Person('P0')
        Presence(person, Subject(), event)
        expected = 'Birth'
        async with self._render(data={
            'event': event,
            'person_context': person,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_person_context_and_other_as_subject(self):
        event = Event(Marriage())
        person = Person('P0')
        other_person = Person('P1')
        Presence(person, Subject(), event)
        Presence(other_person, Subject(), event)
        expected = 'Marriage with <a href="/person/P1/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
        async with self._render(data={
            'event': event,
            'person_context': person,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_subjects(self):
        event = Event(Birth())
        Presence(Person('P0'), Subject(), event)
        Presence(Person('P1'), Subject(), event)
        expected = 'Birth of <a href="/person/P0/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>, <a href="/person/P1/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
        async with self._render(data={
            'event': event,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_without_subjects(self):
        event = Event(Birth())
        expected = 'Birth'
        async with self._render(data={
            'event': event,
        }) as (actual, _):
            self.assertEqual(expected, actual)

    @sync
    async def test_with_resource(self):
        event = Event(Birth())
        expected = 'Birth'
        async with self._render(data={
            'resource': event,
        }) as (actual, _):
            self.assertEqual(expected, actual)
