from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Attendee, Subject
from betty.date import Date
from betty.jinja2 import EntityContexts
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "component/timeline.html.j2"

    async def test_minimal(self) -> None:
        async with self.assert_template_file(
            data={
                "events": [],
            }
        ) as (actual, _):
            assert actual == ""

    async def test_with_minimal_event(self) -> None:
        name = "What's happening?"
        event = Event(name=name, date=Date(1970, 1, 1))
        async with self.assert_template_file(
            data={
                "events": [event],
            }
        ) as (actual, _):
            assert name in actual

    async def test_with_private_event(self) -> None:
        name = "What's happening?"
        event = Event(name=name, date=Date(1970, 1, 1), private=True)
        async with self.assert_template_file(
            data={
                "events": [event],
            }
        ) as (actual, _):
            assert actual == ""

    async def test_with_event_without_date(self) -> None:
        name = "What's happening?"
        event = Event(name=name)
        async with self.assert_template_file(
            data={
                "events": [event],
            }
        ) as (actual, _):
            assert actual == ""

    async def test_with_event_without_comparable_date(self) -> None:
        name = "What's happening?"
        event = Event(name=name, date=Date(None, 1, 1))
        async with self.assert_template_file(
            data={
                "events": [event],
            }
        ) as (actual, _):
            assert actual == ""

    async def test_with_subject_attendee(self) -> None:
        person = Person()
        name = "What's happening?"
        event = Event(name=name, date=Date(1970, 1, 1))
        Presence(person, Subject(), event)
        async with self.assert_template_file(
            data={
                "events": [event],
                "entity_contexts": await EntityContexts.new(person),
            }
        ) as (actual, _):
            assert "timeline-attendee--subject" in actual

    async def test_with_other_attendee(self) -> None:
        person = Person()
        name = "What's happening?"
        event = Event(name=name, date=Date(1970, 1, 1))
        Presence(person, Attendee(), event)
        async with self.assert_template_file(
            data={
                "events": [event],
                "entity_contexts": await EntityContexts.new(person),
            }
        ) as (actual, _):
            assert "timeline-attendee" in actual
