from __future__ import annotations

from typing import Iterable, cast

from betty.locale import DateRange, Date, Datey
from betty.model.ancestry import Person, Presence, Event, Subject
from betty.model.event_type import DerivableEventType, CreatableDerivableEventType, EventType


class DerivedEvent(Event):
    def __init__(self, event_type: type[EventType], date: Datey | None = None):
        super().__init__(None, event_type, date)


class DerivedDate(Date):
    @classmethod
    def derive(cls, date: Date) -> DerivedDate:
        return cls(date.year, date.month, date.day, fuzzy=date.fuzzy)


class Deriver:
    def __init__(self, event_types: set[type[EventType]]):
        self._event_types = event_types

    def derive_person(self, person: Person, event_type: type[DerivableEventType]) -> tuple[int, int]:
        # Gather any existing events that could be derived, or create a new derived event if needed.
        derivable_events = list(_get_derivable_events(person, event_type))
        if not derivable_events:
            if list(filter(
                lambda presence: presence.event is not None and issubclass(presence.event.type, event_type),
                person.presences,
            )):
                return 0, 0
            if issubclass(event_type, CreatableDerivableEventType):
                derivable_events = [DerivedEvent(event_type)]
            else:
                return 0, 0

        # Aggregate event type order from references and backreferences.
        comes_before_event_types = event_type.comes_before()
        comes_after_event_types = event_type.comes_after()
        for other_event_type in self._event_types:
            if event_type in other_event_type.comes_before():
                comes_after_event_types.add(other_event_type)
            if event_type in other_event_type.comes_after():
                comes_before_event_types.add(other_event_type)

        created_derivations = 0
        updated_derivations = 0

        for derivable_event in derivable_events:
            dates_derived = False
            # We know _get_derivable_events() only returns events without a date or a with a date range, but Python
            # does not let us express that in a(n intersection) type, so we must instead cast here.
            derivable_date = cast('DateRange | None', derivable_event.date)

            if derivable_date is None or derivable_date.end is None:
                dates_derived = dates_derived or _ComesBeforeDateDeriver.derive(person, derivable_event, comes_before_event_types)

            if derivable_date is None or derivable_date.start is None:
                dates_derived = dates_derived or _ComesAfterDateDeriver.derive(person, derivable_event, comes_after_event_types)

            if dates_derived:
                if isinstance(derivable_event, DerivedEvent):
                    created_derivations += 1
                    Presence(person, Subject(), derivable_event)
                else:
                    updated_derivations += 1

        return created_derivations, updated_derivations


class _DateDeriver:
    @classmethod
    def derive(cls, person: Person, derivable_event: Event, reference_event_types: set[type[EventType]]) -> bool:
        if not reference_event_types:
            return False

        reference_events = _get_reference_events(person, reference_event_types)
        reference_events_dates: Iterable[tuple[Event, Date]] = filter(
            lambda x: x[1].comparable,
            cls._get_events_dates(reference_events)
        )
        if derivable_event.date is not None:
            reference_events_dates = filter(lambda x: cls._compare(cast(DateRange, derivable_event.date), x[1]), reference_events_dates)
        reference_events_dates = cls._sort(reference_events_dates)
        try:
            reference_event, reference_date = reference_events_dates[0]
        except IndexError:
            return False

        if derivable_event.date is None:
            derivable_event.date = DateRange()
        cls._set(cast(DateRange, derivable_event.date), DerivedDate.derive(reference_date))
        derivable_event.citations.add(*reference_event.citations)

        return True

    @classmethod
    def _get_events_dates(cls, events: Iterable[Event]) -> Iterable[tuple[Event, Date]]:
        for event in events:
            if isinstance(event.date, Date):
                yield event, event.date
            if isinstance(event.date, DateRange):
                for date in cls._get_date_range_dates(event.date):
                    yield event, date

    @classmethod
    def _get_date_range_dates(cls, date: DateRange) -> Iterable[Date]:
        raise NotImplementedError(repr(cls))

    @classmethod
    def _compare(cls, derivable_date: DateRange, reference_date: Date) -> bool:
        raise NotImplementedError(repr(cls))

    @classmethod
    def _sort(cls, events_dates: Iterable[tuple[Event, Date]]) -> list[tuple[Event, Date]]:
        raise NotImplementedError(repr(cls))

    @classmethod
    def _set(cls, derivable_date: DateRange, derived_date: DerivedDate) -> None:
        raise NotImplementedError(repr(cls))


class _ComesBeforeDateDeriver(_DateDeriver):
    @classmethod
    def _get_date_range_dates(cls, date: DateRange) -> Iterable[Date]:
        if date.start is not None and not date.start_is_boundary:
            yield date.start
        if date.end is not None:
            yield date.end

    @classmethod
    def _compare(cls, derivable_date: DateRange, reference_date: Date) -> bool:
        return derivable_date < reference_date

    @classmethod
    def _sort(cls, events_dates: Iterable[tuple[Event, Date]]) -> list[tuple[Event, Date]]:
        return sorted(events_dates, key=lambda x: x[1])

    @classmethod
    def _set(cls, derivable_date: DateRange, derived_date: DerivedDate) -> None:
        derivable_date.end = derived_date
        derivable_date.end_is_boundary = True


class _ComesAfterDateDeriver(_DateDeriver):
    @classmethod
    def _get_date_range_dates(cls, date: DateRange) -> Iterable[Date]:
        if date.start is not None:
            yield date.start
        if date.end is not None and not date.end_is_boundary:
            yield date.end

    @classmethod
    def _compare(cls, derivable_date: DateRange, reference_date: Date) -> bool:
        return derivable_date > reference_date

    @classmethod
    def _sort(cls, events_dates: Iterable[tuple[Event, Date]]) -> list[tuple[Event, Date]]:
        return sorted(events_dates, key=lambda x: x[1], reverse=True)

    @classmethod
    def _set(cls, derivable_date: DateRange, derived_date: DerivedDate) -> None:
        derivable_date.start = derived_date
        derivable_date.start_is_boundary = True


def _get_derivable_events(person: Person, derivable_event_type: type[EventType]) -> Iterable[Event]:
    for presence in person.presences:
        event = presence.event

        if event is None:
            continue

        # Ignore events that have been derived already.
        if isinstance(event, DerivedEvent):
            continue

        # Ignore events of the wrong type.
        if not issubclass(event.type, derivable_event_type):
            continue

        # Ignore events with enough date information that nothing more can be derived.
        if isinstance(event.date, Date):
            continue
        if isinstance(event.date, DateRange) and (not event.type.comes_after() or event.date.start is not None) and (not event.type.comes_before() or event.date.end is not None):
            continue

        yield event


def _get_reference_events(person: Person, reference_event_types: set[type[EventType]]) -> Iterable[Event]:
    for presence in person.presences:
        reference_event = presence.event

        if reference_event is None:
            continue

        # We cannot reliably determine dates based on reference events with calculated date ranges, as those events
        # would start or end *sometime* during the date range, but to derive dates we need reference events' exact
        # start and end dates.
        if isinstance(reference_event, DerivedEvent):
            continue

        # Ignore reference events of the wrong type.
        if not issubclass(reference_event.type, tuple(reference_event_types)):
            continue

        yield reference_event
