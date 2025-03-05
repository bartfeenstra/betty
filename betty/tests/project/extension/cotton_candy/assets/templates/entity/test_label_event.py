from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Birth, Marriage
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Subject, Witness
from betty.jinja2 import EntityContexts
from betty.project.extension.cotton_candy import CottonCandy
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    event = Event(event_type=Birth())
    expected = "Birth"
    async with assert_template_file(
        data={
            "entity": event,
        },
        extensions={CottonCandy},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_identifiable() -> None:
    event = Event(
        id="E0",
        event_type=Birth(),
    )
    expected = '<a href="/event/E0/index.html">Birth</a>'
    async with assert_template_file(
        data={
            "entity": event,
        },
        extensions={CottonCandy},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_embedded_with_identifiable() -> None:
    event = Event(
        id="E0",
        event_type=Birth(),
    )
    Presence(Person(id="P0"), Subject(), event)
    expected = (
        'Birth of <span class="nn" title="This person\'s name is unknown.">n.n.</span>'
    )
    async with assert_template_file(
        data={
            "entity": event,
            "embedded": True,
        },
        extensions={CottonCandy},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_description() -> None:
    event = Event(
        event_type=Birth(),
        description="Something happened!",
    )
    expected = "Birth (Something happened!)"
    async with assert_template_file(
        data={
            "entity": event,
        },
        extensions={CottonCandy},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_witnesses() -> None:
    event = Event(event_type=Birth())
    Presence(Person(id="P0"), Witness(), event)
    expected = "Birth"
    async with assert_template_file(
        data={
            "entity": event,
        },
        extensions={CottonCandy},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_person_context_as_subject() -> None:
    event = Event(event_type=Birth())
    person = Person(id="P0")
    Presence(person, Subject(), event)
    expected = "Birth"
    async with assert_template_file(
        data={
            "entity": event,
            "entity_contexts": await EntityContexts.new(person),
        },
        extensions={CottonCandy},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_person_context_and_other_as_subject() -> None:
    event = Event(event_type=Marriage())
    person = Person(id="P0")
    other_person = Person(id="P1")
    Presence(person, Subject(), event)
    Presence(other_person, Subject(), event)
    expected = 'Marriage with <a href="/person/P1/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
    async with assert_template_file(
        data={
            "entity": event,
            "entity_contexts": await EntityContexts.new(person),
        },
        extensions={CottonCandy},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_subjects() -> None:
    event = Event(event_type=Birth())
    Presence(Person(id="P0"), Subject(), event)
    Presence(Person(id="P1"), Subject(), event)
    expected = 'Birth of <a href="/person/P0/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>, <a href="/person/P1/index.html"><span class="nn" title="This person\'s name is unknown.">n.n.</span></a>'
    async with assert_template_file(
        data={
            "entity": event,
        },
        extensions={CottonCandy},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_without_subjects() -> None:
    event = Event(event_type=Birth())
    expected = "Birth"
    async with assert_template_file(
        data={
            "entity": event,
        },
        extensions={CottonCandy},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_entity() -> None:
    event = Event(event_type=Birth())
    expected = "Birth"
    async with assert_template_file(
        data={
            "entity": event,
        },
        extensions={CottonCandy},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected
