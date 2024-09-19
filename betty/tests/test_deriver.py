from __future__ import annotations

import pytest

from betty.deriver import Deriver
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.date import DateRange, Date, Datey
from betty.model.collections import record_added
from betty.ancestry import Person, Presence, Event, Ancestry
from betty.ancestry.presence_role.presence_roles import Subject
from betty.ancestry.event_type.event_types import (
    DerivableEventType,
    CreatableDerivableEventType,
)
from betty.project.config import DEFAULT_LIFETIME_THRESHOLD
from betty.test_utils.ancestry.event_type import DummyEventType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.ancestry.event_type import EventType


class Ignored(DummyEventType):
    pass


class ComesBeforeReference(DummyEventType):
    pass


class ComesAfterReference(DummyEventType):
    pass


class ComesBeforeDerivable(DummyEventType, DerivableEventType):
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {ComesBeforeReference}


class ComesBeforeCreatableDerivable(ComesBeforeDerivable, CreatableDerivableEventType):
    pass


class ComesAfterDerivable(DummyEventType, DerivableEventType):
    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {ComesAfterReference}


class ComesAfterCreatableDerivable(ComesAfterDerivable, CreatableDerivableEventType):
    pass


class ComesBeforeAndAfterDerivable(DummyEventType, DerivableEventType):
    @classmethod
    def comes_before(cls) -> set[type[EventType]]:
        return {Ignored}

    @classmethod
    def comes_after(cls) -> set[type[EventType]]:
        return {Ignored}


class ComesBeforeAndAfterCreatableDerivable(
    DummyEventType, CreatableDerivableEventType
):
    pass


class MayNotCreateComesAfterCreatableDerivable(ComesAfterCreatableDerivable):
    @classmethod
    def may_create(cls, person: Person, lifetime_threshold: int) -> bool:
        return False


_EVENT_TYPES: set[type[DerivableEventType]] = {
    ComesBeforeDerivable,
    ComesBeforeCreatableDerivable,
    ComesAfterDerivable,
    ComesAfterCreatableDerivable,
    ComesBeforeAndAfterDerivable,
    ComesBeforeAndAfterCreatableDerivable,
}


class TestDeriver:
    @pytest.mark.parametrize(
        "event_type",
        [
            ComesBeforeDerivable,
            ComesBeforeCreatableDerivable,
            ComesAfterDerivable,
            ComesAfterCreatableDerivable,
            ComesBeforeAndAfterDerivable,
            ComesBeforeAndAfterCreatableDerivable,
        ],
    )
    async def test_derive_without_events(
        self, event_type: type[DerivableEventType]
    ) -> None:
        person = Person(id="P0")
        ancestry = Ancestry()
        ancestry.add(person)

        with record_added(ancestry) as added:
            await Deriver(
                ancestry,
                DEFAULT_LIFETIME_THRESHOLD,
                _EVENT_TYPES,
                localizer=DEFAULT_LOCALIZER,
            ).derive()

        assert len(added) == 0
        assert len(person.presences) == 0

    @pytest.mark.parametrize(
        "event_type",
        [
            ComesBeforeDerivable,
            ComesBeforeCreatableDerivable,
            ComesAfterDerivable,
            ComesAfterCreatableDerivable,
            ComesBeforeAndAfterDerivable,
            ComesBeforeAndAfterCreatableDerivable,
        ],
    )
    async def test_derive_create_derivable_events_without_reference_events(
        self, event_type: type[DerivableEventType]
    ) -> None:
        person = Person(id="P0")
        derivable_event = Event(event_type=Ignored())
        Presence(person, Subject(), derivable_event)
        ancestry = Ancestry()
        ancestry.add(person)

        with record_added(ancestry) as added:
            await Deriver(
                ancestry,
                DEFAULT_LIFETIME_THRESHOLD,
                _EVENT_TYPES,
                localizer=DEFAULT_LOCALIZER,
            ).derive()

        assert len(added) == 0
        assert len(person.presences) == 1
        assert derivable_event.date is None

    @pytest.mark.parametrize(
        "event_type",
        [
            ComesBeforeDerivable(),
            ComesBeforeCreatableDerivable(),
            ComesAfterDerivable(),
            ComesAfterCreatableDerivable(),
            ComesBeforeAndAfterDerivable(),
            ComesBeforeAndAfterCreatableDerivable(),
        ],
    )
    async def test_derive_update_derivable_event_without_reference_events(
        self, event_type: DerivableEventType
    ) -> None:
        person = Person(id="P0")
        Presence(person, Subject(), Event(event_type=Ignored()))
        derivable_event = Event(event_type=event_type)
        Presence(person, Subject(), derivable_event)
        ancestry = Ancestry()
        ancestry.add(person)

        with record_added(ancestry) as added:
            await Deriver(
                ancestry,
                DEFAULT_LIFETIME_THRESHOLD,
                _EVENT_TYPES,
                localizer=DEFAULT_LOCALIZER,
            ).derive()

        assert len(added) == 0
        assert derivable_event.date is None

    @pytest.mark.parametrize(
        ("expected_datey", "before_datey", "derivable_datey"),
        [
            (None, None, None),
            (Date(2000, 1, 1), Date(1970, 1, 1), Date(2000, 1, 1)),
            (Date(1969, 1, 1), Date(1970, 1, 1), Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1970, 1, 1), end_is_boundary=True),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1)),
            ),
            (
                DateRange(None, Date(2000, 1, 1)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                None,
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                None,
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                Date(1970, 1, 1),
                None,
            ),
            (Date(2000, 1, 1), DateRange(Date(1970, 1, 1)), Date(2000, 1, 1)),
            (Date(1969, 1, 1), DateRange(Date(1970, 1, 1)), Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1970, 1, 1), end_is_boundary=True),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1)),
            ),
            (
                DateRange(None, Date(2000, 1, 1)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(None, Date(2000, 1, 1)),
                None,
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                None,
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                Date(1970, 1, 1),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                Date(1970, 1, 1),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                DateRange(Date(1970, 1, 1)),
                None,
            ),
            (Date(2000, 1, 1), DateRange(None, Date(1970, 1, 1)), Date(2000, 1, 1)),
            (Date(1969, 1, 1), DateRange(None, Date(1970, 1, 1)), Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1970, 1, 1), end_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(1969, 1, 1)),
            ),
            (DateRange(Date(2000, 1, 1)), None, DateRange(Date(2000, 1, 1))),
            (DateRange(Date(1969, 1, 1)), None, DateRange(Date(1969, 1, 1))),
            (
                DateRange(None, Date(2000, 1, 1)),
                Date(1970, 1, 1),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                Date(1970, 1, 1),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                DateRange(None, Date(1970, 1, 1)),
                None,
            ),
            (
                Date(2000, 1, 1),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                Date(2000, 1, 1),
            ),
            (
                Date(1969, 1, 1),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                Date(1969, 1, 1),
            ),
            (Date(2000, 1, 1), None, Date(2000, 1, 1)),
            (Date(1969, 1, 1), None, Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                Date(1970, 1, 1),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1970, 1, 1), end_is_boundary=True),
                Date(1970, 1, 1),
                DateRange(Date(1969, 1, 1)),
            ),
            (
                DateRange(None, Date(2000, 1, 1)),
                DateRange(Date(1970, 1, 1)),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                DateRange(Date(1970, 1, 1)),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                None,
            ),
        ],
    )
    async def test_derive_update_comes_before_derivable_event(
        self,
        expected_datey: Datey | None,
        before_datey: Datey | None,
        derivable_datey: Datey | None,
    ) -> None:
        person = Person(id="P0")
        Presence(
            person,
            Subject(),
            Event(
                event_type=Ignored(),
                date=Date(0, 0, 0),
            ),
        )
        Presence(
            person,
            Subject(),
            Event(
                event_type=ComesBeforeReference(),
                date=before_datey,
            ),
        )
        derivable_event = Event(
            event_type=ComesBeforeDerivable(),
            date=derivable_datey,
        )
        Presence(person, Subject(), derivable_event)
        ancestry = Ancestry()
        ancestry.add(person)

        with record_added(ancestry) as added:
            await Deriver(
                ancestry,
                DEFAULT_LIFETIME_THRESHOLD,
                {ComesBeforeDerivable},
                localizer=DEFAULT_LOCALIZER,
            ).derive()

        assert len(added) == 0
        if expected_datey is None:
            assert expected_datey == derivable_event.date

    @pytest.mark.parametrize(
        ("expected_datey", "before_datey"),
        [
            (
                None,
                None,
            ),
            (DateRange(None, Date(1970, 1, 1), end_is_boundary=True), Date(1970, 1, 1)),
            (None, DateRange(None, None)),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                DateRange(Date(1970, 1, 1)),
            ),
            (None, DateRange(Date(1970, 1, 1, fuzzy=True))),
            (None, DateRange(None, Date(1970, 1, 1))),
            (
                DateRange(None, Date(1970, 1, 1), end_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1971, 1, 1)),
            ),
        ],
    )
    async def test_derive_create_comes_before_derivable_event(
        self,
        expected_datey: Datey | None,
        before_datey: Datey | None,
    ) -> None:
        person = Person(id="P0")
        Presence(
            person,
            Subject(),
            Event(
                event_type=Ignored(),
                date=Date(0, 0, 0),
            ),
        )
        Presence(
            person,
            Subject(),
            Event(
                event_type=ComesBeforeReference(),
                date=before_datey,
            ),
        )
        ancestry = Ancestry()
        ancestry.add(person)

        with record_added(ancestry) as added:
            await Deriver(
                ancestry,
                DEFAULT_LIFETIME_THRESHOLD,
                {ComesBeforeCreatableDerivable},
                localizer=DEFAULT_LOCALIZER,
            ).derive()

        if expected_datey is None:
            assert len(added) == 0
        else:
            assert len(added[Event]) > 0
            for derived_event in added[Event]:
                assert isinstance(
                    derived_event.event_type, ComesBeforeCreatableDerivable
                )

            assert len(added[Presence]) > 0
            for derived_presence in added[Presence]:
                assert isinstance(derived_presence.role, Subject)
                assert derived_presence.event is not None
                assert isinstance(
                    derived_presence.event.event_type, ComesBeforeCreatableDerivable
                )
                assert expected_datey == derived_presence.event.date

    @pytest.mark.parametrize(
        ("expected_datey", "after_datey", "derivable_datey"),
        [
            (None, None, None),
            (Date(2000, 1, 1), Date(1970, 1, 1), Date(2000, 1, 1)),
            (Date(1969, 1, 1), Date(1970, 1, 1), Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1)),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(1970, 1, 1), Date(2000, 1, 1), start_is_boundary=True),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                None,
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                None,
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(Date(1970, 1, 1), start_is_boundary=True),
                Date(1970, 1, 1),
                None,
            ),
            (Date(2000, 1, 1), DateRange(Date(1970, 1, 1)), Date(2000, 1, 1)),
            (Date(1969, 1, 1), DateRange(Date(1970, 1, 1)), Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(1999, 12, 31), Date(2000, 1, 1), start_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(None, Date(2000, 1, 1)),
                None,
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                None,
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                Date(1970, 1, 1),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                Date(1970, 1, 1),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(Date(1970, 1, 1), start_is_boundary=True),
                DateRange(Date(1970, 1, 1)),
                None,
            ),
            (Date(2000, 1, 1), DateRange(None, Date(1970, 1, 1)), Date(2000, 1, 1)),
            (Date(1969, 1, 1), DateRange(None, Date(1970, 1, 1)), Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1)),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                DateRange(Date(1969, 1, 1)),
            ),
            (DateRange(Date(2000, 1, 1)), None, DateRange(Date(2000, 1, 1))),
            (DateRange(Date(1969, 1, 1)), None, DateRange(Date(1969, 1, 1))),
            (
                DateRange(Date(1970, 1, 1), Date(2000, 1, 1), start_is_boundary=True),
                Date(1970, 1, 1),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                Date(1970, 1, 1),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                DateRange(Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(Date(1970, 1, 1), start_is_boundary=True),
                DateRange(None, Date(1970, 1, 1)),
                None,
            ),
            (
                Date(2000, 1, 1),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                Date(2000, 1, 1),
            ),
            (
                Date(1969, 1, 1),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                Date(1969, 1, 1),
            ),
            (Date(2000, 1, 1), None, Date(2000, 1, 1)),
            (Date(1969, 1, 1), None, Date(1969, 1, 1)),
            (
                DateRange(Date(2000, 1, 1)),
                Date(1970, 1, 1),
                DateRange(Date(2000, 1, 1)),
            ),
            (
                DateRange(Date(1969, 1, 1)),
                Date(1970, 1, 1),
                DateRange(Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(1970, 1, 1), Date(2000, 1, 1), start_is_boundary=True),
                DateRange(Date(1970, 1, 1)),
                DateRange(None, Date(2000, 1, 1)),
            ),
            (
                DateRange(None, Date(1969, 1, 1)),
                DateRange(Date(1970, 1, 1)),
                DateRange(None, Date(1969, 1, 1)),
            ),
            (
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(2000, 1, 1), Date(2000, 12, 31)),
            ),
            (
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
                DateRange(None, Date(1970, 1, 1)),
                DateRange(Date(1969, 1, 1), Date(1969, 12, 31)),
            ),
            (
                DateRange(Date(1999, 12, 31), start_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
                None,
            ),
        ],
    )
    async def test_derive_update_comes_after_derivable_event(
        self,
        expected_datey: Datey | None,
        after_datey: Datey | None,
        derivable_datey: Datey | None,
    ) -> None:
        person = Person(id="P0")
        Presence(
            person,
            Subject(),
            Event(
                event_type=Ignored(),
                date=Date(0, 0, 0),
            ),
        )
        Presence(
            person,
            Subject(),
            Event(
                event_type=ComesAfterReference(),
                date=after_datey,
            ),
        )
        derivable_event = Event(
            event_type=ComesAfterDerivable(),
            date=derivable_datey,
        )
        Presence(person, Subject(), derivable_event)
        ancestry = Ancestry()
        ancestry.add(person)

        with record_added(ancestry) as added:
            await Deriver(
                ancestry,
                DEFAULT_LIFETIME_THRESHOLD,
                {ComesAfterDerivable},
                localizer=DEFAULT_LOCALIZER,
            ).derive()

        assert len(added) == 0
        if expected_datey is None:
            assert expected_datey == derivable_event.date

    @pytest.mark.parametrize(
        ("expected_datey", "after_datey"),
        [
            (None, None),
            (None, Date()),
            (DateRange(Date(1970, 1, 1), start_is_boundary=True), Date(1970, 1, 1)),
            (None, DateRange(Date(1970, 1, 1))),
            (
                DateRange(Date(1999, 12, 31), start_is_boundary=True),
                DateRange(None, Date(1999, 12, 31)),
            ),
            (None, DateRange(None, Date(1999, 12, 31, fuzzy=True))),
            (
                DateRange(Date(1999, 12, 31), start_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),
            ),
            (
                DateRange(Date(1970, 1, 1), start_is_boundary=True),
                DateRange(Date(1970, 1, 1), Date(1999, 12, 31), end_is_boundary=True),
            ),
        ],
    )
    async def test_derive_create_comes_after_derivable_event(
        self,
        expected_datey: Datey | None,
        after_datey: Datey | None,
    ) -> None:
        person = Person(id="P0")
        Presence(
            person,
            Subject(),
            Event(
                event_type=Ignored(),
                date=Date(0, 0, 0),
            ),
        )
        Presence(
            person,
            Subject(),
            Event(
                event_type=ComesAfterReference(),
                date=after_datey,
            ),
        )
        ancestry = Ancestry()
        ancestry.add(person)

        with record_added(ancestry) as added:
            await Deriver(
                ancestry,
                DEFAULT_LIFETIME_THRESHOLD,
                {ComesAfterCreatableDerivable},
                localizer=DEFAULT_LOCALIZER,
            ).derive()

        if expected_datey is None:
            assert len(added) == 0
        else:
            assert len(added[Event]) > 0
            for derived_event in added[Event]:
                assert isinstance(
                    derived_event.event_type, ComesAfterCreatableDerivable
                )

            assert len(added[Presence]) > 0
            for derived_presence in added[Presence]:
                assert isinstance(derived_presence.role, Subject)
                assert derived_presence.event is not None
                assert isinstance(
                    derived_presence.event.event_type, ComesAfterCreatableDerivable
                )
                assert expected_datey == derived_presence.event.date

    @pytest.mark.parametrize(
        "after_datey",
        [
            (None,),
            (Date(),),
            (Date(1970, 1, 1),),
            (DateRange(Date(1970, 1, 1)),),
            (DateRange(None, Date(1999, 12, 31)),),
            (DateRange(Date(1970, 1, 1), Date(1999, 12, 31)),),
            (DateRange(Date(1970, 1, 1), Date(1999, 12, 31), end_is_boundary=True),),
        ],
    )
    async def test_derive_may_not_create(
        self,
        after_datey: Datey | None,
    ) -> None:
        person = Person(id="P0")
        presence = Presence(
            person,
            Subject(),
            Event(
                event_type=ComesAfterReference(),
                date=after_datey,
            ),
        )
        ancestry = Ancestry()
        ancestry.add(person)

        with record_added(ancestry) as added:
            await Deriver(
                ancestry,
                DEFAULT_LIFETIME_THRESHOLD,
                {MayNotCreateComesAfterCreatableDerivable},
                localizer=DEFAULT_LOCALIZER,
            ).derive()

        assert len(added) == 0
        assert [*person.presences] == [presence]
