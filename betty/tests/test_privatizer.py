from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.locale.date import Date, DateRange
from betty.model.ancestry import (
    Person,
    Presence,
    Event,
    Source,
    File,
    Citation,
    Privacy,
    Place,
    Enclosure,
    FileReference,
)
from betty.model.presence_role import Subject, Attendee
from betty.model.event_type import Death, Birth, Marriage
from betty.privatizer import Privatizer
from betty.project import DEFAULT_LIFETIME_THRESHOLD
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def _expand_person(generation: int) -> list[tuple[bool, Privacy, Event | None]]:
    multiplier = abs(generation) + 1 if generation < 0 else 1
    lifetime_threshold_year = (
        datetime.now().year - DEFAULT_LIFETIME_THRESHOLD * multiplier
    )
    date_under_lifetime_threshold = Date(lifetime_threshold_year + 1, 1, 1)
    date_range_start_under_lifetime_threshold = DateRange(date_under_lifetime_threshold)
    date_range_end_under_lifetime_threshold = DateRange(
        None, date_under_lifetime_threshold
    )
    date_over_lifetime_threshold = Date(lifetime_threshold_year - 1, 1, 1)
    date_range_start_over_lifetime_threshold = DateRange(date_over_lifetime_threshold)
    date_range_end_over_lifetime_threshold = DateRange(
        None, date_over_lifetime_threshold
    )
    return [
        # If there are no events for a person, they are private.
        (True, Privacy.UNDETERMINED, None),
        (True, Privacy.PRIVATE, None),
        (False, Privacy.PUBLIC, None),
        # Deaths and other end-of-life events are special, but only for the person whose privacy is being checked:
        # - If they're present without dates, the person isn't private.
        # - If they're present and their dates or date ranges' end dates are in the past, the person isn't private.
        (
            generation != 0,
            Privacy.UNDETERMINED,
            Event(
                event_type=Death,
                date=Date(
                    datetime.now().year, datetime.now().month, datetime.now().day
                ),
            ),
        ),
        (
            generation != 0,
            Privacy.UNDETERMINED,
            Event(
                event_type=Death,
                date=date_under_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.UNDETERMINED,
            Event(
                event_type=Death,
                date=date_range_start_under_lifetime_threshold,
            ),
        ),
        (
            generation != 0,
            Privacy.UNDETERMINED,
            Event(
                event_type=Death,
                date=date_range_end_under_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.UNDETERMINED,
            Event(
                event_type=Death,
                date=date_over_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.UNDETERMINED,
            Event(
                event_type=Death,
                date=date_range_start_over_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.UNDETERMINED,
            Event(
                event_type=Death,
                date=date_range_end_over_lifetime_threshold,
            ),
        ),
        (True, Privacy.PRIVATE, Event(event_type=Death)),
        (False, Privacy.PUBLIC, Event(event_type=Death)),
        (generation != 0, Privacy.UNDETERMINED, Event(event_type=Death)),
        # Regular events without dates do not affect privacy.
        (True, Privacy.UNDETERMINED, Event(event_type=Birth)),
        (True, Privacy.PRIVATE, Event(event_type=Birth)),
        (False, Privacy.PUBLIC, Event(event_type=Birth)),
        # Regular events with incomplete dates do not affect privacy.
        (
            True,
            Privacy.UNDETERMINED,
            Event(
                event_type=Birth,
                date=Date(),
            ),
        ),
        (
            True,
            Privacy.PRIVATE,
            Event(
                event_type=Birth,
                date=Date(),
            ),
        ),
        (
            False,
            Privacy.PUBLIC,
            Event(
                event_type=Birth,
                date=Date(),
            ),
        ),
        # Regular events under the lifetime threshold do not affect privacy.
        (
            True,
            Privacy.UNDETERMINED,
            Event(
                event_type=Birth,
                date=date_under_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.PRIVATE,
            Event(
                event_type=Birth,
                date=date_under_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.PUBLIC,
            Event(
                event_type=Birth,
                date=date_under_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.UNDETERMINED,
            Event(
                event_type=Birth,
                date=date_range_start_under_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.PRIVATE,
            Event(
                event_type=Birth,
                date=date_range_start_under_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.PUBLIC,
            Event(
                event_type=Birth,
                date=date_range_start_under_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.UNDETERMINED,
            Event(
                event_type=Birth,
                date=date_range_end_under_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.PRIVATE,
            Event(
                event_type=Birth,
                date=date_range_end_under_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.PUBLIC,
            Event(
                event_type=Birth,
                date=date_range_end_under_lifetime_threshold,
            ),
        ),
        # Regular events over the lifetime threshold affect privacy.
        (
            False,
            Privacy.UNDETERMINED,
            Event(
                event_type=Birth,
                date=date_over_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.PRIVATE,
            Event(
                event_type=Birth,
                date=date_over_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.PUBLIC,
            Event(
                event_type=Birth,
                date=date_over_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.UNDETERMINED,
            Event(
                event_type=Birth,
                date=date_range_start_over_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.PRIVATE,
            Event(
                event_type=Birth,
                date=date_range_start_over_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.PUBLIC,
            Event(
                event_type=Birth,
                date=date_range_start_over_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.UNDETERMINED,
            Event(
                event_type=Birth,
                date=date_range_end_over_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.PRIVATE,
            Event(
                event_type=Birth,
                date=date_range_end_over_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.PUBLIC,
            Event(
                event_type=Birth,
                date=date_range_end_over_lifetime_threshold,
            ),
        ),
    ]


class TestPrivatizer:
    async def test_privatize_person_should_not_privatize_if_public(self) -> None:
        citation = Citation(source=Source())
        file = File(path=Path(__file__))
        person = Person(public=True)
        person.citations.add(citation)
        FileReference(person, file)
        presence_as_subject = Presence(person, Subject(), Event(event_type=Birth))
        presence_as_attendee = Presence(person, Attendee(), Event(event_type=Marriage))
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            person
        )
        assert person.public
        assert citation.privacy is Privacy.UNDETERMINED
        assert file.privacy is Privacy.UNDETERMINED
        assert presence_as_subject.privacy is Privacy.UNDETERMINED
        assert presence_as_attendee.privacy is Privacy.UNDETERMINED

    async def test_privatize_person_should_privatize_if_private(self) -> None:
        citation = Citation(source=Source())
        file = File(path=Path(__file__))
        person = Person(private=True)
        person.citations.add(citation)
        FileReference(person, file)
        presence_as_subject = Presence(person, Subject(), Event(event_type=Birth))
        presence_as_attendee = Presence(person, Attendee(), Event(event_type=Marriage))
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            person
        )
        assert person.private
        assert citation.private
        assert file.private
        assert presence_as_subject.private
        assert presence_as_attendee.private

    @pytest.mark.parametrize(("expected", "privacy", "event"), _expand_person(0))
    async def test_privatize_person_without_relatives(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(privacy=privacy)
        if event is not None:
            Presence(person, Subject(), event)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            person
        )
        assert expected == person.private

    @pytest.mark.parametrize(("expected", "privacy", "event"), _expand_person(1))
    async def test_privatize_person_with_child(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(privacy=privacy)
        child = Person()
        if event is not None:
            Presence(child, Subject(), event)
        person.children.add(child)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            person
        )
        assert expected == person.private

    @pytest.mark.parametrize(("expected", "privacy", "event"), _expand_person(2))
    async def test_privatize_person_with_grandchild(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(privacy=privacy)
        child = Person()
        person.children.add(child)
        grandchild = Person()
        if event is not None:
            Presence(grandchild, Subject(), event)
        child.children.add(grandchild)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            person
        )
        assert expected == person.private

    @pytest.mark.parametrize(("expected", "privacy", "event"), _expand_person(3))
    async def test_privatize_person_with_great_grandchild(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(privacy=privacy)
        child = Person()
        person.children.add(child)
        grandchild = Person()
        child.children.add(grandchild)
        great_grandchild = Person()
        if event is not None:
            Presence(great_grandchild, Subject(), event)
        grandchild.children.add(great_grandchild)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            person
        )
        assert expected == person.private

    @pytest.mark.parametrize(("expected", "privacy", "event"), _expand_person(-1))
    async def test_privatize_person_with_parent(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(privacy=privacy)
        parent = Person()
        if event is not None:
            Presence(parent, Subject(), event)
        person.parents.add(parent)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            person
        )
        assert expected == person.private

    @pytest.mark.parametrize(("expected", "privacy", "event"), _expand_person(-2))
    async def test_privatize_person_with_grandparent(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(privacy=privacy)
        parent = Person()
        person.parents.add(parent)
        grandparent = Person()
        if event is not None:
            Presence(grandparent, Subject(), event)
        parent.parents.add(grandparent)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            person
        )
        assert expected == person.private

    @pytest.mark.parametrize(("expected", "privacy", "event"), _expand_person(-3))
    async def test_privatize_person_with_great_grandparent(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(privacy=privacy)
        parent = Person()
        person.parents.add(parent)
        grandparent = Person()
        parent.parents.add(grandparent)
        great_grandparent = Person()
        if event is not None:
            Presence(great_grandparent, Subject(), event)
        grandparent.parents.add(great_grandparent)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            person
        )
        assert expected == person.private

    async def test_privatize_event_should_not_privatize_if_public(self) -> None:
        citation = Citation(source=Source())
        event_file = File(path=Path(__file__))
        event = Event(
            event_type=Birth,
            public=True,
        )
        event.citations.add(citation)
        FileReference(event, event_file)
        person = Person()
        presence = Presence(person, Subject(), event)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            event
        )
        assert not event.private
        assert event_file.privacy is Privacy.UNDETERMINED
        assert citation.privacy is Privacy.UNDETERMINED
        assert presence.privacy is Privacy.UNDETERMINED

    async def test_privatize_event_should_privatize_if_private(self) -> None:
        citation = Citation(source=Source())
        file = File(
            path=Path(__file__),
        )
        event = Event(
            event_type=Birth,
            private=True,
        )
        event.citations.add(citation)
        FileReference(event, file)
        person = Person()
        presence = Presence(person, Subject(), event)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            event
        )
        assert event.private
        assert presence.private
        assert file.private
        assert citation.private

    async def test_privatize_source_should_not_privatize_if_public(self) -> None:
        file = File(
            path=Path(__file__),
        )
        source = Source(
            name="The Source",
            public=True,
        )
        FileReference(source, file)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            source
        )
        assert not source.private
        assert file.privacy is Privacy.UNDETERMINED

    async def test_privatize_source_should_privatize_if_private(self) -> None:
        file = File(
            path=Path(__file__),
        )
        source = Source(
            name="The Source",
            private=True,
        )
        FileReference(source, file)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            source
        )
        assert source.private
        assert file.private

    async def test_privatize_citation_should_not_privatize_if_public(self) -> None:
        file = File(
            path=Path(__file__),
        )
        citation = Citation(
            source=Source(),
            public=True,
        )
        FileReference(citation, file)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            citation
        )
        assert citation.public
        assert file.privacy is Privacy.UNDETERMINED

    async def test_privatize_citation_should_privatize_if_private(self) -> None:
        file = File(
            path=Path(__file__),
        )
        citation = Citation(
            source=Source(),
            private=True,
        )
        FileReference(citation, file)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            citation
        )
        assert citation.private
        assert file.private

    async def test_privatize_file_should_not_privatize_if_public(self) -> None:
        citation = Citation(source=Source())
        file = File(
            path=Path(__file__),
            public=True,
        )
        file.citations.add(citation)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            file
        )
        assert file.public
        assert citation.privacy is Privacy.UNDETERMINED

    async def test_privatize_file_should_privatize_if_private(self) -> None:
        citation = Citation(source=Source())
        file = File(
            path=Path(__file__),
            private=True,
        )
        file.citations.add(citation)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            file
        )
        assert file.private
        assert citation.private

    @pytest.mark.parametrize(
        ("expected", "privacy", "events", "encloses"),
        [
            (Privacy.PUBLIC, Privacy.PUBLIC, [], []),
            (Privacy.PRIVATE, Privacy.PRIVATE, [], []),
            (Privacy.PRIVATE, Privacy.UNDETERMINED, [], []),
            (
                Privacy.UNDETERMINED,
                Privacy.UNDETERMINED,
                [
                    Event(public=True),
                    Event(private=True),
                ],
                [],
            ),
            (Privacy.PRIVATE, Privacy.UNDETERMINED, [Event(private=True)], []),
            (
                Privacy.PRIVATE,
                Privacy.UNDETERMINED,
                [],
                [
                    Enclosure(None, None),
                ],
            ),
            (
                Privacy.UNDETERMINED,
                Privacy.UNDETERMINED,
                [],
                [
                    Enclosure(Place(public=True), None),
                ],
            ),
            (
                Privacy.PRIVATE,
                Privacy.UNDETERMINED,
                [],
                [
                    Enclosure(Place(private=True), None),
                ],
            ),
        ],
    )
    async def test_privatize_place_should_determine_privacy(
        self,
        expected: Privacy,
        privacy: Privacy,
        events: Sequence[Event],
        encloses: Sequence[Enclosure],
    ) -> None:
        place = Place(
            privacy=privacy,
            events=events,
            encloses=encloses,
        )
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            place
        )
        assert place.privacy is expected

    async def test_privatize_place_should_privatize_enclosed_by(self) -> None:
        enclosed_by = Place()
        place = Place(
            private=True,
            enclosed_by=[Enclosure(None, enclosed_by)],
        )
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            place
        )
        assert enclosed_by.private

    async def test_privatize_place_should_not_privatize_public_enclosed_by(
        self,
    ) -> None:
        enclosed_by = Place(public=True)
        place = Place(
            private=True,
            enclosed_by=[Enclosure(None, enclosed_by)],
        )
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            place
        )
        assert enclosed_by.privacy is Privacy.PUBLIC

    async def test_privatize_place_should_not_privatize_enclosed_by_with_public_associations(
        self,
    ) -> None:
        enclosed_by = Place(
            encloses=[Enclosure(Place(), None)],
        )
        place = Place(
            private=True,
            enclosed_by=[Enclosure(None, enclosed_by)],
        )
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            place
        )
        assert enclosed_by.privacy is not Privacy.PRIVATE

    async def test_privatize_place_should_privatize_encloses(self) -> None:
        encloses = Place()
        place = Place(
            private=True,
            encloses=[Enclosure(encloses, None)],
        )
        Privatizer(DEFAULT_LIFETIME_THRESHOLD, localizer=DEFAULT_LOCALIZER).privatize(
            place
        )
        assert encloses.private
