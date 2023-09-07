from betty.extension import CottonCandy
from betty.jinja2 import EntityContexts
from betty.model.ancestry import Person, Event, Presence, Subject, Witness
from betty.model.event_type import Birth, Marriage
from betty.tests import TemplateTestCase


class Test(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = 'entity/label--event.html.j2'

    def test_minimal(self) -> None:
        event = Event(None, Birth)
        expected = 'Birth'
        with self._render(data={
            'entity': event,
        }) as (actual, _):
            assert expected == actual

    def test_with_identifiable(self) -> None:
        event = Event('E0', Birth)
        expected = '<a href="/event/E0/index.html">Birth</a>'
        with self._render(data={
            'entity': event,
        }) as (actual, _):
            assert expected == actual

    def test_embedded_with_identifiable(self) -> None:
        event = Event('E0', Birth)
        Presence(None, Person('P0'), Subject(), event)
        expected = 'Birth of <span class="nn" title="This person\'s name is unknown.">n.n.</span>'
        with self._render(data={
            'entity': event,
            'embedded': True,
        }) as (actual, _):
            assert expected == actual

    def test_with_description(self) -> None:
        event = Event(None, Birth)
        event.description = 'Something happened!'
        expected = 'Birth (Something happened!)'
        with self._render(data={
            'entity': event,
        }) as (actual, _):
            assert expected == actual

    def test_with_witnesses(self) -> None:
        event = Event(None, Birth)
        Presence(None, Person('P0'), Witness(), event)
        expected = 'Birth'
        with self._render(data={
            'entity': event,
        }) as (actual, _):
            assert expected == actual

    def test_with_person_context_as_subject(self) -> None:
        event = Event(None, Birth)
        person = Person('P0')
        Presence(None, person, Subject(), event)
        expected = 'Birth'
        with self._render(data={
            'entity': event,
            'entity_contexts': EntityContexts(person),
        }) as (actual, _):
            assert expected == actual

    def test_with_person_context_and_other_as_subject(self) -> None:
        event = Event(None, Marriage)
        person = Person('P0')
        other_person = Person('P1')
        Presence(None, person, Subject(), event)
        Presence(None, other_person, Subject(), event)
        expected = 'Marriage with <a href="/person/P1/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
        with self._render(data={
            'entity': event,
            'entity_contexts': EntityContexts(person),
        }) as (actual, _):
            assert expected == actual

    def test_with_subjects(self) -> None:
        event = Event(None, Birth)
        Presence(None, Person('P0'), Subject(), event)
        Presence(None, Person('P1'), Subject(), event)
        expected = 'Birth of <a href="/person/P0/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>, <a href="/person/P1/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
        with self._render(data={
            'entity': event,
        }) as (actual, _):
            assert expected == actual

    def test_without_subjects(self) -> None:
        event = Event(None, Birth)
        expected = 'Birth'
        with self._render(data={
            'entity': event,
        }) as (actual, _):
            assert expected == actual

    def test_with_entity(self) -> None:
        event = Event(None, Birth)
        expected = 'Birth'
        with self._render(data={
            'entity': event,
        }) as (actual, _):
            assert expected == actual
