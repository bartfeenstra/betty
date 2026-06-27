from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from betty.date import Date, DateRange
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.presence import Presence
from betty.event_types.birth import Birth
from betty.event_types.death import Death
from betty.event_types.marriage import Marriage
from betty.lifetime import Lifetime, default_lifetime_threshold
from betty.privacy import Privacy
from betty.privacy.privatizer import Privatizer
from betty.roles.subject import Subject
from betty.roles.unknown import UnknownRole
from betty.test_utils.user import StaticUser

if TYPE_CHECKING:
    from collections.abc import Sequence


def _expand_person(generation: int) -> Sequence[tuple[bool, Privacy, Event | None]]:
    multiplier = abs(generation) + 1 if generation < 0 else 1
    lifetime_threshold_year = (
        datetime.now(tz=UTC).year - default_lifetime_threshold * multiplier
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
        # Deaths and other end-of-life events are special, but only for the current generation.
        (
            generation != 0,
            Privacy.UNDETERMINED,
            Event(
                event_type=Death(),
                date=Date(
                    datetime.now(tz=UTC).year,
                    datetime.now(tz=UTC).month,
                    datetime.now(tz=UTC).day,
                ),
            ),
        ),
        (
            generation != 0,
            Privacy.UNDETERMINED,
            Event(
                event_type=Death(),
                date=date_under_lifetime_threshold,
            ),
        ),
        (
            generation != 0,
            Privacy.UNDETERMINED,
            Event(
                event_type=Death(),
                date=date_range_start_under_lifetime_threshold,
            ),
        ),
        (
            generation != 0,
            Privacy.UNDETERMINED,
            Event(
                event_type=Death(),
                date=date_range_end_under_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.UNDETERMINED,
            Event(
                event_type=Death(),
                date=date_over_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.UNDETERMINED,
            Event(
                event_type=Death(),
                date=date_range_start_over_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.UNDETERMINED,
            Event(
                event_type=Death(),
                date=date_range_end_over_lifetime_threshold,
            ),
        ),
        (True, Privacy.PRIVATE, Event(event_type=Death())),
        (False, Privacy.PUBLIC, Event(event_type=Death())),
        (generation != 0, Privacy.UNDETERMINED, Event(event_type=Death())),
        # Regular events without dates do not affect privacy.
        (True, Privacy.UNDETERMINED, Event(event_type=Birth())),
        (True, Privacy.PRIVATE, Event(event_type=Birth())),
        (False, Privacy.PUBLIC, Event(event_type=Birth())),
        # Regular events with incomplete dates do not affect privacy.
        (
            True,
            Privacy.UNDETERMINED,
            Event(
                event_type=Birth(),
                date=Date(),
            ),
        ),
        (
            True,
            Privacy.PRIVATE,
            Event(
                event_type=Birth(),
                date=Date(),
            ),
        ),
        (
            False,
            Privacy.PUBLIC,
            Event(
                event_type=Birth(),
                date=Date(),
            ),
        ),
        # Regular events under the lifetime threshold do not affect privacy.
        (
            True,
            Privacy.UNDETERMINED,
            Event(
                event_type=Birth(),
                date=date_under_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.PRIVATE,
            Event(
                event_type=Birth(),
                date=date_under_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.PUBLIC,
            Event(
                event_type=Birth(),
                date=date_under_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.UNDETERMINED,
            Event(
                event_type=Birth(),
                date=date_range_start_under_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.PRIVATE,
            Event(
                event_type=Birth(),
                date=date_range_start_under_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.PUBLIC,
            Event(
                event_type=Birth(),
                date=date_range_start_under_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.UNDETERMINED,
            Event(
                event_type=Birth(),
                date=date_range_end_under_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.PRIVATE,
            Event(
                event_type=Birth(),
                date=date_range_end_under_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.PUBLIC,
            Event(
                event_type=Birth(),
                date=date_range_end_under_lifetime_threshold,
            ),
        ),
        # Regular events over the lifetime threshold affect privacy.
        (
            False,
            Privacy.UNDETERMINED,
            Event(
                event_type=Birth(),
                date=date_over_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.PRIVATE,
            Event(
                event_type=Birth(),
                date=date_over_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.PUBLIC,
            Event(
                event_type=Birth(),
                date=date_over_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.UNDETERMINED,
            Event(
                event_type=Birth(),
                date=date_range_start_over_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.PRIVATE,
            Event(
                event_type=Birth(),
                date=date_range_start_over_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.PUBLIC,
            Event(
                event_type=Birth(),
                date=date_range_start_over_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.UNDETERMINED,
            Event(
                event_type=Birth(),
                date=date_range_end_over_lifetime_threshold,
            ),
        ),
        (
            True,
            Privacy.PRIVATE,
            Event(
                event_type=Birth(),
                date=date_range_end_over_lifetime_threshold,
            ),
        ),
        (
            False,
            Privacy.PUBLIC,
            Event(
                event_type=Birth(),
                date=date_range_end_over_lifetime_threshold,
            ),
        ),
    ]


class TestPrivatizer:
    sut = Privatizer(lifetime=Lifetime(), user=StaticUser())

    async def test_privatize__person_should_not_privatize_if_public(self) -> None:
        person = Person(privacy=Privacy.PUBLIC)
        presence_as_subject = Presence(person, Subject(), Event(event_type=Birth()))
        presence_as_unknown = Presence(
            person, UnknownRole(), Event(event_type=Marriage())
        )
        await self.sut.privatize(person)
        assert person.privacy is Privacy.PUBLIC
        assert presence_as_subject.privacy is Privacy.UNDETERMINED
        assert presence_as_unknown.privacy is Privacy.UNDETERMINED

    async def test_privatize__person_should_privatize_if_private(self) -> None:
        person = Person(privacy=Privacy.PRIVATE)
        presence_as_subject = Presence(person, Subject(), Event(event_type=Birth()))
        presence_as_unknown = Presence(
            person, UnknownRole(), Event(event_type=Marriage())
        )
        await self.sut.privatize(person)
        assert person.privacy is Privacy.PRIVATE
        assert presence_as_subject.privacy is Privacy.PRIVATE
        assert presence_as_unknown.privacy is Privacy.PRIVATE

    @pytest.mark.parametrize(("expected", "privacy", "event"), _expand_person(0))
    async def test_privatize__person_without_relatives(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(privacy=privacy)
        if event is not None:
            Presence(person, Subject(), event)
        await self.sut.privatize(person)
        if expected:
            assert person.privacy is Privacy.PRIVATE
        else:
            assert person.privacy is not Privacy.PRIVATE

    @pytest.mark.parametrize(("expected", "privacy", "event"), _expand_person(1))
    async def test_privatize__person_with_child(
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
        await self.sut.privatize(person)
        if expected:
            assert person.privacy is Privacy.PRIVATE
        else:
            assert person.privacy is not Privacy.PRIVATE

    @pytest.mark.parametrize(("expected", "privacy", "event"), _expand_person(2))
    async def test_privatize__person_with_grandchild(
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
        await self.sut.privatize(person)
        if expected:
            assert person.privacy is Privacy.PRIVATE
        else:
            assert person.privacy is not Privacy.PRIVATE

    @pytest.mark.parametrize(("expected", "privacy", "event"), _expand_person(3))
    async def test_privatize__person_with_great_grandchild(
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
        await self.sut.privatize(person)
        if expected:
            assert person.privacy is Privacy.PRIVATE
        else:
            assert person.privacy is not Privacy.PRIVATE

    @pytest.mark.parametrize(("expected", "privacy", "event"), _expand_person(-1))
    async def test_privatize__person_with_parent(
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
        await self.sut.privatize(person)
        if expected:
            assert person.privacy is Privacy.PRIVATE
        else:
            assert person.privacy is not Privacy.PRIVATE

    @pytest.mark.parametrize(("expected", "privacy", "event"), _expand_person(-2))
    async def test_privatize__person_with_grandparent(
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
        await self.sut.privatize(person)
        if expected:
            assert person.privacy is Privacy.PRIVATE
        else:
            assert person.privacy is not Privacy.PRIVATE

    @pytest.mark.parametrize(("expected", "privacy", "event"), _expand_person(-3))
    async def test_privatize__person_with_great_grandparent(
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
        await self.sut.privatize(person)
        if expected:
            assert person.privacy is Privacy.PRIVATE
        else:
            assert person.privacy is not Privacy.PRIVATE
