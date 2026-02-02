from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.date import Date
from betty.document import Document, EntityContexts
from betty.extension.raspberry_mint import RaspberryMint
from betty.presence_role.presence_roles import Attendee, Subject
from betty.privacy import Privacy
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    async with assert_template_file(
        data={
            "events": [],
        },
        extensions={RaspberryMint},
        template="component/raspberry-mint/timeline.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_minimal_event() -> None:
    name = "What's happening?"
    event = Event(name=name, date=Date(1970, 1, 1))
    async with assert_template_file(
        data={
            "events": [event],
        },
        extensions={RaspberryMint},
        template="component/raspberry-mint/timeline.html.j2",
    ) as (actual, _):
        assert name in actual


async def test_with_private_event() -> None:
    name = "What's happening?"
    event = Event(name=name, date=Date(1970, 1, 1), privacy=Privacy.PRIVATE)
    async with assert_template_file(
        data={
            "events": [event],
        },
        extensions={RaspberryMint},
        template="component/raspberry-mint/timeline.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_event_without_date() -> None:
    name = "What's happening?"
    event = Event(name=name)
    async with assert_template_file(
        data={
            "events": [event],
        },
        extensions={RaspberryMint},
        template="component/raspberry-mint/timeline.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_event_without_comparable_date() -> None:
    name = "What's happening?"
    event = Event(name=name, date=Date(None, 1, 1))
    async with assert_template_file(
        data={
            "events": [event],
        },
        extensions={RaspberryMint},
        template="component/raspberry-mint/timeline.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_subject_attendee() -> None:
    person = Person()
    name = "What's happening?"
    event = Event(name=name, date=Date(1970, 1, 1))
    Presence(person, Subject(), event)
    async with assert_template_file(
        data={
            "events": [event],
            "document": Document(entity_contexts=EntityContexts(person)),
        },
        extensions={RaspberryMint},
        template="component/raspberry-mint/timeline.html.j2",
    ) as (actual, _):
        assert "timeline-attendee--subject" in actual


async def test_with_other_attendee() -> None:
    person = Person()
    name = "What's happening?"
    event = Event(name=name, date=Date(1970, 1, 1))
    Presence(person, Attendee(), event)
    async with assert_template_file(
        data={
            "events": [event],
            "document": Document(entity_contexts=EntityContexts(person)),
        },
        extensions={RaspberryMint},
        template="component/raspberry-mint/timeline.html.j2",
    ) as (actual, _):
        assert "timeline-attendee" in actual
