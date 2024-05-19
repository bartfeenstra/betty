import pytest

from betty.app import App
from betty.extension import CottonCandy
from betty.jinja2 import EntityContexts
from betty.model.ancestry import Person, Event, Presence, Subject, Witness
from betty.model.event_type import Birth, Marriage
from betty.tests import TemplateTester


class Test:
    @pytest.fixture
    def template_tester(self, new_temporary_app: App) -> TemplateTester:
        new_temporary_app.project.configuration.extensions.enable(CottonCandy)
        return TemplateTester(
            new_temporary_app, template_file="entity/label--event.html.j2"
        )

    async def test_minimal(self, template_tester: TemplateTester) -> None:
        event = Event(event_type=Birth)
        expected = "Birth"
        async with template_tester.render(
            data={
                "entity": event,
            }
        ) as actual:
            assert expected == actual

    async def test_with_identifiable(self, template_tester: TemplateTester) -> None:
        event = Event(
            id="E0",
            event_type=Birth,
        )
        expected = '<a href="/event/E0/index.html">Birth</a>'
        async with template_tester.render(
            data={
                "entity": event,
            }
        ) as actual:
            assert expected == actual

    async def test_embedded_with_identifiable(
        self, template_tester: TemplateTester
    ) -> None:
        event = Event(
            id="E0",
            event_type=Birth,
        )
        Presence(Person(id="P0"), Subject(), event)
        expected = 'Birth of <span class="nn" title="This person\'s name is unknown.">n.n.</span>'
        async with template_tester.render(
            data={
                "entity": event,
                "embedded": True,
            }
        ) as actual:
            assert expected == actual

    async def test_with_description(self, template_tester: TemplateTester) -> None:
        event = Event(
            event_type=Birth,
            description="Something happened!",
        )
        expected = "Birth (Something happened!)"
        async with template_tester.render(
            data={
                "entity": event,
            }
        ) as actual:
            assert expected == actual

    async def test_with_witnesses(self, template_tester: TemplateTester) -> None:
        event = Event(event_type=Birth)
        Presence(Person(id="P0"), Witness(), event)
        expected = "Birth"
        async with template_tester.render(
            data={
                "entity": event,
            }
        ) as actual:
            assert expected == actual

    async def test_with_person_context_as_subject(
        self, template_tester: TemplateTester
    ) -> None:
        event = Event(event_type=Birth)
        person = Person(id="P0")
        Presence(person, Subject(), event)
        expected = "Birth"
        async with template_tester.render(
            data={
                "entity": event,
                "entity_contexts": EntityContexts(person),
            }
        ) as actual:
            assert expected == actual

    async def test_with_person_context_and_other_as_subject(
        self, template_tester: TemplateTester
    ) -> None:
        event = Event(event_type=Marriage)
        person = Person(id="P0")
        other_person = Person(id="P1")
        Presence(person, Subject(), event)
        Presence(other_person, Subject(), event)
        expected = 'Marriage with <a href="/person/P1/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
        async with template_tester.render(
            data={
                "entity": event,
                "entity_contexts": EntityContexts(person),
            }
        ) as actual:
            assert expected == actual

    async def test_with_subjects(self, template_tester: TemplateTester) -> None:
        event = Event(event_type=Birth)
        Presence(Person(id="P0"), Subject(), event)
        Presence(Person(id="P1"), Subject(), event)
        expected = 'Birth of <a href="/person/P0/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>, <a href="/person/P1/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
        async with template_tester.render(
            data={
                "entity": event,
            }
        ) as actual:
            assert expected == actual

    async def test_without_subjects(self, template_tester: TemplateTester) -> None:
        event = Event(event_type=Birth)
        expected = "Birth"
        async with template_tester.render(
            data={
                "entity": event,
            }
        ) as actual:
            assert expected == actual

    async def test_with_entity(self, template_tester: TemplateTester) -> None:
        event = Event(event_type=Birth)
        expected = "Birth"
        async with template_tester.render(
            data={
                "entity": event,
            }
        ) as actual:
            assert expected == actual
