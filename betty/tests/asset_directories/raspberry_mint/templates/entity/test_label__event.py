from betty.document import Document, EntityContexts
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.presence import Presence
from betty.event_types.birth import Birth
from betty.event_types.marriage import Marriage
from betty.roles.subject import Subject
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    event = Event(event_type=Birth())
    expected = "Birth"
    async with assert_raspberry_mint_jinja_file(
        "entity/label--event.html.j2", data={"entity": event}
    ) as rendered:
        assert rendered == expected


async def test_with_name(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    event = Event(
        event_type=Birth(),
        name="Something happened!",
    )
    expected = '<span lang="und" dir="auto">Something happened!</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--event.html.j2", data={"entity": event}
    ) as rendered:
        assert rendered == expected


async def test_with_persistent_id(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    event = Event(
        id="my-first-event",
        event_type=Birth(),
        name="Something happened!",
    )
    expected = f'<a href="/event/{event.id}/index.html"><span lang="und" dir="auto">Something happened!</span></a>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--event.html.j2", data={"entity": event}
    ) as rendered:
        assert rendered == expected


async def test_with_embedded(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    event = Event(
        id="my-first-event",
        event_type=Birth(),
        name="Something happened!",
    )
    expected = '<span lang="und" dir="auto">Something happened!</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--event.html.j2", data={"entity": event, "embedded": True}
    ) as rendered:
        assert rendered == expected


async def test_with_single_subject_as_person_context(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    event = Event(event_type=Marriage())
    context_subject = Person()
    Presence(context_subject, Subject(), event)
    expected = "Marriage"
    async with assert_raspberry_mint_jinja_file(
        "entity/label--event.html.j2",
        data={
            "entity": event,
            "document": Document(entity_contexts=EntityContexts(context_subject)),
        },
    ) as rendered:
        assert rendered == expected


async def test_with_subjects_and_subject_as_person_context(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    event = Event(event_type=Marriage())
    context_subject = Person()
    other_subject = Person()
    Presence(context_subject, Subject(), event)
    Presence(other_subject, Subject(), event)
    expected = 'Marriage with <span title="This person\'s name is unknown.">n.n.</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--event.html.j2",
        data={
            "entity": event,
            "document": Document(entity_contexts=EntityContexts(context_subject)),
        },
    ) as rendered:
        assert rendered == expected


async def test_with_subjects_without_person_context(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    event = Event(event_type=Marriage())
    context_subject = Person()
    other_subject = Person()
    Presence(context_subject, Subject(), event)
    Presence(other_subject, Subject(), event)
    expected = 'Marriage of <span title="This person\'s name is unknown.">n.n.</span> and <span title="This person\'s name is unknown.">n.n.</span>'
    async with assert_raspberry_mint_jinja_file(
        "entity/label--event.html.j2", data={"entity": event}
    ) as rendered:
        assert rendered == expected
