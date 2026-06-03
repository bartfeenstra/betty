from betty.asset_directories.raspberry_mint import RASPBERRY_MINT
from betty.date import Date
from betty.document import Document, EntityContexts
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.presence import Presence
from betty.privacy import Privacy
from betty.roles.attendee import Attendee
from betty.roles.subject import Subject
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    async with assert_template_file(
        data={
            "events": [],
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/timeline.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_minimal_event(assert_template_file: AssertTemplateFile) -> None:
    name = "What's happening?"
    event = Event(name=name, date=Date(1970, 1, 1))
    async with assert_template_file(
        data={
            "events": [event],
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/timeline.html.j2",
    ) as (actual, _):
        assert name in actual


async def test_with_private_event(assert_template_file: AssertTemplateFile) -> None:
    name = "What's happening?"
    event = Event(name=name, date=Date(1970, 1, 1), privacy=Privacy.PRIVATE)
    async with assert_template_file(
        data={
            "events": [event],
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/timeline.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_event_without_date(
    assert_template_file: AssertTemplateFile,
) -> None:
    name = "What's happening?"
    event = Event(name=name)
    async with assert_template_file(
        data={
            "events": [event],
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/timeline.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_event_without_comparable_date(
    assert_template_file: AssertTemplateFile,
) -> None:
    name = "What's happening?"
    event = Event(name=name, date=Date(None, 1, 1))
    async with assert_template_file(
        data={
            "events": [event],
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/timeline.html.j2",
    ) as (actual, _):
        assert actual == ""


async def test_with_subject_attendee(assert_template_file: AssertTemplateFile) -> None:
    person = Person()
    name = "What's happening?"
    event = Event(name=name, date=Date(1970, 1, 1))
    Presence(person, Subject(), event)
    async with assert_template_file(
        data={
            "events": [event],
            "document": Document(entity_contexts=EntityContexts(person)),
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/timeline.html.j2",
    ) as (actual, _):
        assert "timeline-attendee--subject" in actual


async def test_with_other_attendee(assert_template_file: AssertTemplateFile) -> None:
    person = Person()
    name = "What's happening?"
    event = Event(name=name, date=Date(1970, 1, 1))
    Presence(person, Attendee(), event)
    async with assert_template_file(
        data={
            "events": [event],
            "document": Document(entity_contexts=EntityContexts(person)),
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/timeline.html.j2",
    ) as (actual, _):
        assert "timeline-attendee" in actual
