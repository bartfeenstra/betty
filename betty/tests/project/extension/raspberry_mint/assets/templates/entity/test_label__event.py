from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Birth, Marriage
from betty.ancestry.person import Person
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Subject
from betty.jinja2 import EntityContexts
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "entity/label--event.html.j2"

    async def test_minimal(self) -> None:
        event = Event(event_type=Birth())
        expected = "Birth"
        async with self.assert_template_file(
            data={
                "entity": event,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_name(self) -> None:
        event = Event(
            event_type=Birth(),
            name="Something happened!",
        )
        expected = '<span lang="und" dir="auto">Something happened!</span>'
        async with self.assert_template_file(
            data={
                "entity": event,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_persistent_id(self) -> None:
        event_id = "EVENT1"
        event = Event(
            id=event_id,
            event_type=Birth(),
            name="Something happened!",
        )
        expected = '<a href="/event/EVENT1/index.html"><span lang="und" dir="auto">Something happened!</span></a>'
        async with self.assert_template_file(
            data={
                "entity": event,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_embedded(self) -> None:
        event_id = "EVENT1"
        event = Event(
            id=event_id,
            event_type=Birth(),
            name="Something happened!",
        )
        expected = '<span lang="und" dir="auto">Something happened!</span>'
        async with self.assert_template_file(
            data={
                "entity": event,
                "embedded": True,
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_single_subject_as_person_context(self) -> None:
        event = Event(event_type=Marriage())
        context_subject = Person()
        Presence(context_subject, Subject(), event)
        expected = "Marriage"
        async with self.assert_template_file(
            data={
                "entity": event,
                "entity_contexts": await EntityContexts.new(context_subject),
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_subjects_and_subject_as_person_context(self) -> None:
        event = Event(event_type=Marriage())
        context_subject = Person()
        other_subject = Person()
        Presence(context_subject, Subject(), event)
        Presence(other_subject, Subject(), event)
        expected = (
            'Marriage with <span title="This person\'s name is unknown.">n.n.</span>'
        )
        async with self.assert_template_file(
            data={
                "entity": event,
                "entity_contexts": await EntityContexts.new(context_subject),
            }
        ) as (actual, _):
            assert actual == expected

    async def test_with_subjects_without_person_context(self) -> None:
        event = Event(event_type=Marriage())
        context_subject = Person()
        other_subject = Person()
        Presence(context_subject, Subject(), event)
        Presence(other_subject, Subject(), event)
        expected = 'Marriage of <span title="This person\'s name is unknown.">n.n.</span>, <span title="This person\'s name is unknown.">n.n.</span>'
        async with self.assert_template_file(
            data={
                "entity": event,
            }
        ) as (actual, _):
            assert actual == expected
