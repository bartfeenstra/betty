import logging
from typing import List, Tuple, Set, Type, Iterable, Any

from betty.ancestry import Person, Presence, Event, Subject, EventType, EVENT_TYPE_TYPES, DerivableEventType, \
    CreatableDerivableEventType, Ancestry
from betty.locale import DateRange, Date
from betty.parse import PostParser
from betty.plugin import Plugin, NO_CONFIGURATION
from betty.plugin.privatizer import Privatizer
from betty.site import Site


class DerivedEvent(Event):
    pass  # pragma: no cover


class DerivedDate(Date):
    @classmethod
    def derive(cls, date: Date) -> 'DerivedDate':
        return cls(date.year, date.month, date.day, fuzzy=date.fuzzy)


class Deriver(Plugin, PostParser):
    def __init__(self, ancestry: Ancestry):
        self._ancestry = ancestry

    @classmethod
    def for_site(cls, site: Site, configuration: Any = NO_CONFIGURATION):
        return cls(site.ancestry)

    async def post_parse(self,) -> None:
        await self.derive(self._ancestry)

    async def derive(self, ancestry: Ancestry) -> None:
        logger = logging.getLogger()
        for event_type_type in EVENT_TYPE_TYPES:
            event_type = event_type_type()
            if isinstance(event_type, DerivableEventType):
                created_derivations = 0
                updated_derivations = 0
                for person in ancestry.people.values():
                    created, updated = derive(person, event_type_type)
                    created_derivations += created
                    updated_derivations += updated
                logger.info('Updated %d %s events based on existing information.' % (updated_derivations, event_type.label))
                if isinstance(event_type, CreatableDerivableEventType):
                    logger.info('Created %d additional %s events based on existing information.' % (created_derivations, event_type.label))

    @classmethod
    def comes_before(cls) -> Set[Type[Plugin]]:
        return {Privatizer}


class _DateDeriver:
    @classmethod
    def derive(cls, person: Person, derivable_event: Event, reference_event_type_types: Set[Type[EventType]]) -> bool:
        if not reference_event_type_types:
            return False

        reference_events = _get_reference_events(person, reference_event_type_types)
        reference_events_dates = cls._get_events_dates(reference_events)
        reference_events_dates = filter(lambda x: x[1].comparable, reference_events_dates)
        if derivable_event.date is not None:
            reference_events_dates = filter(lambda x: cls._compare(derivable_event.date, x[1]), reference_events_dates)
        reference_events_dates = cls._sort(reference_events_dates)
        try:
            reference_event, reference_date = reference_events_dates[0]
        except IndexError:
            return False

        if derivable_event.date is None:
            derivable_event.date = DateRange()
        cls._set(derivable_event, DerivedDate.derive(reference_date))
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
    def _set(derivable_event: Event, date: DerivedDate) -> None:
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
    def _set(derivable_event: Event, date: DerivedDate) -> None:
        derivable_event.date.end = date
        derivable_event.date.end_is_boundary = True


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
    def _set(derivable_event: Event, date: DerivedDate) -> None:
        derivable_event.date.start = date
        derivable_event.date.start_is_boundary = True


def derive(person: Person, event_type_type: Type[DerivableEventType]) -> Tuple[int, int]:
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
    for other_event_type_type in EVENT_TYPE_TYPES:
        if event_type_type in other_event_type_type.comes_before():
            comes_after_event_type_types.add(other_event_type_type)
        if event_type_type in other_event_type_type.comes_after():
            comes_before_event_type_types.add(other_event_type_type)

    created_derivations = 0
    updated_derivations = 0

    for derivable_event in derivable_events:
        dates_derived = False

        if derivable_event.date is None or derivable_event.date.end is None:
            dates_derived = dates_derived or _ComesBeforeDateDeriver.derive(person, derivable_event, comes_before_event_type_types)

        if derivable_event.date is None or derivable_event.date.start is None:
            dates_derived = dates_derived or _ComesAfterDateDeriver.derive(person, derivable_event, comes_after_event_type_types)

        if dates_derived:
            if isinstance(derivable_event, DerivedEvent):
                created_derivations += 1
                Presence(person, Subject(), derivable_event)
            else:
                updated_derivations += 1

    return created_derivations, updated_derivations


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

        yield presence.event


def _get_reference_events(person: Person, reference_event_type_types: Set[Type[EventType]]) -> Iterable[Event]:
    for reference_event in [presence.event for presence in person.presences]:
        # We cannot reliably determine dates based on reference events with calculated date ranges, as those events
        # would start or end *sometime* during the date range, but to derive dates we need reference events' exact
        # start and end dates.
        if isinstance(reference_event, DerivedEvent):
            continue

        # Ignore reference events of the wrong type.
        if not isinstance(reference_event.type, tuple(reference_event_type_types)):
            continue

        yield reference_event
