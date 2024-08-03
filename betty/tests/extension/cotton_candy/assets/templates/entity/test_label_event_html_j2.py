from betty.extension.cotton_candy import CottonCandy
from betty.jinja2 import EntityContexts
from betty.ancestry import Person, Event, Presence
from betty.ancestry.presence_role import Subject, Witness
from betty.ancestry.event_type import Birth, Marriage
from betty.test_utils.assets.templates import TemplateTestBase


class Test(TemplateTestBase):
    extensions = {CottonCandy}
    template_file = "entity/label--event.html.j2"

    async def test_minimal(self) -> None:
        event = Event(event_type=Birth())
        expected = "Birth"
        async with self._render(
            data={
                "entity": event,
            }
        ) as (actual, _):
            assert expected == actual

    async def test_with_identifiable(self) -> None:
        event = Event(
            id="E0",
            event_type=Birth(),
        )
        expected = '<a href="/event/E0/index.html">Birth</a>'
        async with self._render(
            data={
                "entity": event,
            }
        ) as (actual, _):
            assert expected == actual

    async def test_embedded_with_identifiable(self) -> None:
        event = Event(
            id="E0",
            event_type=Birth(),
        )
        Presence(Person(id="P0"), Subject(), event)
        expected = 'Birth of <span class="nn" title="This person\'s name is unknown.">n.n.</span>'
        async with self._render(
            data={
                "entity": event,
                "embedded": True,
            }
        ) as (actual, _):
            assert expected == actual

    async def test_with_description(self) -> None:
        event = Event(
            event_type=Birth(),
            description="Something happened!",
        )
        expected = "Birth (Something happened!)"
        async with self._render(
            data={
                "entity": event,
            }
        ) as (actual, _):
            assert expected == actual

    async def test_with_witnesses(self) -> None:
        event = Event(event_type=Birth())
        Presence(Person(id="P0"), Witness(), event)
        expected = "Birth"
        async with self._render(
            data={
                "entity": event,
            }
        ) as (actual, _):
            assert expected == actual

    async def test_with_person_context_as_subject(self) -> None:
        event = Event(event_type=Birth())
        person = Person(id="P0")
        Presence(person, Subject(), event)
        expected = "Birth"
        async with self._render(
            data={
                "entity": event,
                "entity_contexts": EntityContexts(person),
            }
        ) as (actual, _):
            assert expected == actual

    async def test_with_person_context_and_other_as_subject(self) -> None:
        event = Event(event_type=Marriage())
        person = Person(id="P0")
        other_person = Person(id="P1")
        Presence(person, Subject(), event)
        Presence(other_person, Subject(), event)
        expected = 'Marriage with <a href="/person/P1/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
        async with self._render(
            data={
                "entity": event,
                "entity_contexts": EntityContexts(person),
            }
        ) as (actual, _):
            assert expected == actual

    async def test_with_subjects(self) -> None:
        event = Event(event_type=Birth())
        Presence(Person(id="P0"), Subject(), event)
        Presence(Person(id="P1"), Subject(), event)
        expected = 'Birth of <a href="/person/P0/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>, <a href="/person/P1/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
        async with self._render(
            data={
                "entity": event,
            }
        ) as (actual, _):
            assert expected == actual

    async def test_without_subjects(self) -> None:
        event = Event(event_type=Birth())
        expected = "Birth"
        async with self._render(
            data={
                "entity": event,
            }
        ) as (actual, _):
            assert expected == actual

    async def test_with_entity(self) -> None:
        event = Event(event_type=Birth())
        expected = "Birth"
        async with self._render(
            data={
                "entity": event,
            }
        ) as (actual, _):
            assert expected == actual
