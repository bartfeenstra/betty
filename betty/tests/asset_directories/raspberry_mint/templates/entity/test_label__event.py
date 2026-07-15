from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.document import Document, EntityContexts
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.presence import Presence
from betty.event_types.birth import Birth
from betty.event_types.marriage import Marriage
from betty.roles.subject import Subject
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    event = Event(event_type=Birth())
    expected = "Birth"
    async with assert_template_file(
        data={
            "entity": event,
        },
        assets={raspberry_mint},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_name(assert_template_file: AssertTemplateFile) -> None:
    event = Event(
        event_type=Birth(),
        name="Something happened!",
    )
    expected = '<span lang="und" dir="auto">Something happened!</span>'
    async with assert_template_file(
        data={
            "entity": event,
        },
        assets={raspberry_mint},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_persistent_id(assert_template_file: AssertTemplateFile) -> None:
    event = Event(
        id="my-first-event",
        event_type=Birth(),
        name="Something happened!",
    )
    expected = f'<a href="/event/{event.id}/index.html"><span lang="und" dir="auto">Something happened!</span></a>'
    async with assert_template_file(
        data={
            "entity": event,
        },
        assets={raspberry_mint},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_embedded(assert_template_file: AssertTemplateFile) -> None:
    event = Event(
        id="my-first-event",
        event_type=Birth(),
        name="Something happened!",
    )
    expected = '<span lang="und" dir="auto">Something happened!</span>'
    async with assert_template_file(
        data={
            "entity": event,
            "embedded": True,
        },
        assets={raspberry_mint},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_single_subject_as_person_context(
    assert_template_file: AssertTemplateFile,
) -> None:
    event = Event(event_type=Marriage())
    context_subject = Person()
    Presence(context_subject, Subject(), event)
    expected = "Marriage"
    async with assert_template_file(
        data={
            "entity": event,
            "document": Document(entity_contexts=EntityContexts(context_subject)),
        },
        assets={raspberry_mint},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_subjects_and_subject_as_person_context(
    assert_template_file: AssertTemplateFile,
) -> None:
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
        assets={raspberry_mint},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected


async def test_with_subjects_without_person_context(
    assert_template_file: AssertTemplateFile,
) -> None:
    event = Event(event_type=Marriage())
    context_subject = Person()
    other_subject = Person()
    Presence(context_subject, Subject(), event)
    Presence(other_subject, Subject(), event)
    expected = 'Marriage of <span title="This person\'s name is unknown.">n.n.</span> and <span title="This person\'s name is unknown.">n.n.</span>'
    async with assert_template_file(
        data={
            "entity": event,
        },
        assets={raspberry_mint},
        template="entity/label--event.html.j2",
    ) as (actual, _):
        assert actual == expected
