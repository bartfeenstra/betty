from __future__ import annotations

import logging
from typing import List, Tuple, Set, Type, Iterable, Optional, TYPE_CHECKING, cast

from betty.app.extension import Extension, UserFacingExtension
from betty.load import PostLoader
from betty.locale import DateRange, Date, Datey
from betty.model.ancestry import Person, Presence, Event, Subject, EventType, Ancestry
from betty.model.event_type import DerivableEventType, CreatableDerivableEventType
from betty.privatizer import Privatizer

if TYPE_CHECKING:
    from betty.builtins import _


class DerivedEvent(Event):
    def __init__(self, event_type: EventType, date: Optional[Datey] = None):
        super().__init__(None, event_type, date)


class DerivedDate(Date):
    @classmethod
    def derive(cls, date: Date) -> DerivedDate:
        return cls(date.year, date.month, date.day, fuzzy=date.fuzzy)


class Deriver(UserFacingExtension, PostLoader):
    async def post_load(self) -> None:
        await self.derive(self.app.project.ancestry)

    async def derive(self, ancestry: Ancestry) -> None:
        logger = logging.getLogger()
        for event_type_type in self.app.event_types:
            event_type = event_type_type()
            if isinstance(event_type, DerivableEventType):
                created_derivations = 0
                updated_derivations = 0
                for person in ancestry.entities[Person]:
                    created, updated = self.derive_person(person, event_type_type)
                    created_derivations += created
                    updated_derivations += updated
                logger.info('Updated %d %s events based on existing information.' % (updated_derivations, event_type.label))
                if isinstance(event_type, CreatableDerivableEventType):
                    logger.info('Created %d additional %s events based on existing information.' % (created_derivations, event_type.label))

    def derive_person(self, person: Person, event_type_type: Type[DerivableEventType]) -> Tuple[int, int]:
        # Gather any existing events that could be derived, or create a new derived event if needed.
        derivable_events = list(_get_derivable_events(person, event_type_type))
        if not derivable_events:
            if list(filter(lambda x: isinstance(x.event.type, event_type_type), person.presences)):
                return 0, 0
            if issubclass(event_type_type, CreatableDerivableEventType):
                derivable_events = [DerivedEvent(event_type_type())]
            else:
                return 0, 0

        # Aggregate event type order from references and backreferences.
        comes_before_event_type_types = event_type_type.comes_before()
        comes_after_event_type_types = event_type_type.comes_after()
        for other_event_type_type in self.app.event_types:
            if event_type_type in other_event_type_type.comes_before():
                comes_after_event_type_types.add(other_event_type_type)
            if event_type_type in other_event_type_type.comes_after():
                comes_before_event_type_types.add(other_event_type_type)

        created_derivations = 0
        updated_derivations = 0

        for derivable_event in derivable_events:
            dates_derived = False
            # We know _get_derivable_events() only returns events without a date or a with a date range, but Python
            # does not let us express that in a(n intersection) type, so we must instead cast here.
            derivable_date = cast(Optional[DateRange], derivable_event.date)

            if derivable_date is None or derivable_date.end is None:
                dates_derived = dates_derived or _ComesBeforeDateDeriver.derive(person, derivable_event, comes_before_event_type_types)

            if derivable_date is None or derivable_date.start is None:
                dates_derived = dates_derived or _ComesAfterDateDeriver.derive(person, derivable_event, comes_after_event_type_types)

            if dates_derived:
                if isinstance(derivable_event, DerivedEvent):
                    created_derivations += 1
                    Presence(person, Subject(), derivable_event)
                else:
                    updated_derivations += 1

        return created_derivations, updated_derivations

    @classmethod
    def comes_before(cls) -> Set[Type[Extension]]:
        return {Privatizer}

    @classmethod
    def label(cls) -> str:
        return _('Deriver')

    @classmethod
    def description(cls) -> str:
        return _('Create events such as births and deaths by deriving their details from existing information.')


class _DateDeriver:
    @classmethod
    def derive(cls, person: Person, derivable_event: Event, reference_event_type_types: Set[Type[EventType]]) -> bool:
        if not reference_event_type_types:
            return False

        reference_events = _get_reference_events(person, reference_event_type_types)
        reference_events_dates: Iterable[Tuple[Event, Date]] = filter(
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
        derivable_event.citations.append(*reference_event.citations)

        return True

    @classmethod
    def _get_events_dates(cls, events: Iterable[Event]) -> Iterable[Tuple[Event, Date]]:
        for event in events:
            if isinstance(event.date, Date):
                yield event, event.date
            if isinstance(event.date, DateRange):
                for date in cls._get_date_range_dates(event.date):
                    yield event, date

    @staticmethod
    def _get_date_range_dates(date: DateRange) -> Iterable[Date]:
        raise NotImplementedError

    @staticmethod
    def _compare(derivable_date: DateRange, reference_date: Date) -> bool:
        raise NotImplementedError

    @staticmethod
    def _sort(events_dates: Iterable[Tuple[Event, Date]]) -> List[Tuple[Event, Date]]:
        raise NotImplementedError

    @staticmethod
    def _set(derivable_date: DateRange, derived_date: DerivedDate) -> None:
        raise NotImplementedError


class _ComesBeforeDateDeriver(_DateDeriver):
    @staticmethod
    def _get_date_range_dates(date: DateRange) -> Iterable[Date]:
        if date.start is not None and not date.start_is_boundary:
            yield date.start
        if date.end is not None:
            yield date.end

    @staticmethod
    def _compare(derivable_date: DateRange, reference_date: Date) -> bool:
        return derivable_date < reference_date

    @staticmethod
    def _sort(events_dates: Iterable[Tuple[Event, Date]]) -> List[Tuple[Event, Date]]:
        return sorted(events_dates, key=lambda x: x[1])

    @staticmethod
    def _set(derivable_date: DateRange, derived_date: DerivedDate) -> None:
        derivable_date.end = derived_date
        derivable_date.end_is_boundary = True


class _ComesAfterDateDeriver(_DateDeriver):
    @staticmethod
    def _get_date_range_dates(date: DateRange) -> Iterable[Date]:
        if date.start is not None:
            yield date.start
        if date.end is not None and not date.end_is_boundary:
            yield date.end

    @staticmethod
    def _compare(derivable_date: DateRange, reference_date: Date) -> bool:
        return derivable_date > reference_date

    @staticmethod
    def _sort(events_dates: Iterable[Tuple[Event, Date]]) -> List[Tuple[Event, Date]]:
        return sorted(events_dates, key=lambda x: x[1], reverse=True)

    @staticmethod
    def _set(derivable_date: DateRange, derived_date: DerivedDate) -> None:
        derivable_date.start = derived_date
        derivable_date.start_is_boundary = True


def _get_derivable_events(person: Person, derivable_event_type_type: Type[EventType]) -> Iterable[Event]:
    for presence in person.presences:
        event = presence.event

        # Ignore events that have been derived already.
        if isinstance(event, DerivedEvent):
            continue

        # Ignore events of the wrong type.
        if not isinstance(event.type, derivable_event_type_type):
            continue

        # Ignore events with enough date information that nothing more can be derived.
        if isinstance(event.date, Date):
            continue
        if isinstance(event.date, DateRange) and (not event.type.comes_after() or event.date.start is not None) and (not event.type.comes_before() or event.date.end is not None):
            continue

        yield event


def _get_reference_events(person: Person, reference_event_type_types: Set[Type[EventType]]) -> Iterable[Event]:
    for reference_event in (presence.event for presence in person.presences):
        # We cannot reliably determine dates based on reference events with calculated date ranges, as those events
        # would start or end *sometime* during the date range, but to derive dates we need reference events' exact
        # start and end dates.
        if isinstance(reference_event, DerivedEvent):
            continue

        # Ignore reference events of the wrong type.
        if not isinstance(reference_event.type, tuple(reference_event_type_types)):
            continue

        yield reference_event
