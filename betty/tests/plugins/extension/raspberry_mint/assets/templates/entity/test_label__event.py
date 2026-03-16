from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.document import Document, EntityContexts
from betty.plugins.event_type import Birth, Marriage
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.plugins.role import Subject
from betty.test_utils.jinja import assert_template_file


async def test_minimal() -> None:
    event = Event(event_type=Birth())
    expected = "Birth"
    async with assert_template_file(
        data={
            "entity": event,
        },
        extensions={RaspberryMint},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_name() -> None:
    event = Event(
        event_type=Birth(),
        name="Something happened!",
    )
    expected = '<span lang="und" dir="auto">Something happened!</span>'
    async with assert_template_file(
        data={
            "entity": event,
        },
        extensions={RaspberryMint},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_persistent_id() -> None:
    event = Event(
        id="EVENT1",
        event_type=Birth(),
        name="Something happened!",
    )
    expected = f'<a href="/event/{event.public_id}/index.html"><span lang="und" dir="auto">Something happened!</span></a>'
    async with assert_template_file(
        data={
            "entity": event,
        },
        extensions={RaspberryMint},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_embedded() -> None:
    event_id = "EVENT1"
    event = Event(
        id=event_id,
        event_type=Birth(),
        name="Something happened!",
    )
    expected = '<span lang="und" dir="auto">Something happened!</span>'
    async with assert_template_file(
        data={
            "entity": event,
            "embedded": True,
        },
        extensions={RaspberryMint},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_single_subject_as_person_context() -> None:
    event = Event(event_type=Marriage())
    context_subject = Person()
    Presence(context_subject, Subject(), event)
    expected = "Marriage"
    async with assert_template_file(
        data={
            "entity": event,
            "document": Document(entity_contexts=EntityContexts(context_subject)),
        },
        extensions={RaspberryMint},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_subjects_and_subject_as_person_context() -> None:
    event = Event(event_type=Marriage())
    context_subject = Person()
    other_subject = Person()
    Presence(context_subject, Subject(), event)
    Presence(other_subject, Subject(), event)
    expected = 'Marriage with <span title="This person\'s name is unknown.">n.n.</span>'
    async with assert_template_file(
        data={
            "entity": event,
            "document": Document(entity_contexts=EntityContexts(context_subject)),
        },
        extensions={RaspberryMint},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_subjects_without_person_context() -> None:
    event = Event(event_type=Marriage())
    context_subject = Person()
    other_subject = Person()
    Presence(context_subject, Subject(), event)
    Presence(other_subject, Subject(), event)
    expected = 'Marriage of <span title="This person\'s name is unknown.">n.n.</span>, <span title="This person\'s name is unknown.">n.n.</span>'
    async with assert_template_file(
        data={
            "entity": event,
        },
        extensions={RaspberryMint},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected
