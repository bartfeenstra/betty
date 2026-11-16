from betty.date import Date
from betty.document import Document, EntityContexts
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.presence import Presence
from betty.privacy import Privacy
from betty.roles.attendee import Attendee
from betty.roles.subject import Subject
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/timeline.html.j2", data={"events": []}
    ) as rendered:
        assert rendered == ""


async def test_with_minimal_event(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    name = "What's happening?"
    event = Event(name=name, date=Date(1970, 1, 1))
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/timeline.html.j2", data={"events": [event]}
    ) as rendered:
        assert name in rendered


async def test_with_private_event(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    name = "What's happening?"
    event = Event(name=name, date=Date(1970, 1, 1), privacy=Privacy.PRIVATE)
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/timeline.html.j2", data={"events": [event]}
    ) as rendered:
        assert rendered == ""


async def test_with_event_without_date(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    name = "What's happening?"
    event = Event(name=name)
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/timeline.html.j2", data={"events": [event]}
    ) as rendered:
        assert rendered == ""


async def test_with_event_without_comparable_date(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    name = "What's happening?"
    event = Event(name=name, date=Date(None, 1, 1))
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/timeline.html.j2", data={"events": [event]}
    ) as rendered:
        assert rendered == ""


async def test_with_subject_attendee(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    person = Person()
    name = "What's happening?"
    event = Event(name=name, date=Date(1970, 1, 1))
    Presence(person, Subject(), event)
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/timeline.html.j2",
        data={
            "events": [event],
            "document": Document(entity_contexts=EntityContexts(person)),
        },
    ) as rendered:
        assert "timeline-attendee--subject" in rendered


async def test_with_other_attendee(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    person = Person()
    name = "What's happening?"
    event = Event(name=name, date=Date(1970, 1, 1))
    Presence(person, Attendee(), event)
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/timeline.html.j2",
        data={
            "events": [event],
            "document": Document(entity_contexts=EntityContexts(person)),
        },
    ) as rendered:
        assert "timeline-attendee" in rendered
