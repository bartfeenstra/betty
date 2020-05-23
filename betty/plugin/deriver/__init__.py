import logging
from collections import defaultdict
from contextlib import suppress
from copy import copy
from typing import List, Tuple, Callable, Optional, Set, Type, Iterable

from betty.ancestry import Ancestry, Person, Presence, Event, Subject, EventType, EVENT_TYPES, DerivableEventType, \
    CreatableDerivableEventType
from betty.event import Event as DispatchedEvent
from betty.locale import DateRange, Datey
from betty.parse import PostParseEvent
from betty.plugin import Plugin
from betty.plugin.cleaner import Cleaner


class DerivedEvent(Event):
    pass  # pragma: no cover


class Deriver(Plugin):
    def subscribes_to(self) -> List[Tuple[Type[DispatchedEvent], Callable]]:
        return [
            (PostParseEvent, self._derive),
        ]

    async def _derive(self, event: PostParseEvent) -> None:
        derivations = defaultdict(lambda: 0)
        try:
            for event_type in EVENT_TYPES:
                if isinstance(event_type, DerivableEventType):
                    for person in event.ancestry.people.values():
                        derivations[event_type] += int(derive(person, event_type))
        finally:
            logger = logging.getLogger()
            for event_type in EVENT_TYPES:
                logger.info('Created %d additional %s events derived from existing information.' % (derivations[event_type], event_type.label))

    @classmethod
    def comes_after(cls) -> Set[Type[Plugin]]:
        return {Cleaner}


def derive(person: Person, event_type: EventType) -> None:
    # @todo 1) Do we want to derive events from other derived events? Initial gut feeling says no.
    # @todo 2) We want to be able to mark date ranges as "this event took place sometime in this date range".
    # @todo     This is not neccesarily an estimate. Can we mark them as "calculated", like Gramps does?
    # @todo
    # @todo
    # @todo
    derived_events = list(filter(_event_is_complete, _get_primary_events(person, type(event_type))))
    for derived_event in derived_events:
        if derived_event.date is None:
            derived_event.date = DateRange()
    if not derived_events and isinstance(event_type, CreatableDerivableEventType):
        derived_events = [DerivedEvent(event_type, DateRange())]
    else:
        return

    derived = False
    if event_type.comes_before() and derived_event.date.end is None:
        event_dates = _get_event_dates(person, event_type.comes_before())
        event_dates = sorted(event_dates, key=lambda x: x[1])
        with suppress(IndexError):
            reference_event, reference_date = event_dates[0]
            derived_event.date.end = copy(reference_date)
            _update_event(reference_event, derived_event)
            derived = True
    if event_type.comes_after() and derived_event.date.start is None:
        event_dates = _get_event_dates(person, event_type.comes_after())
        event_dates = sorted(event_dates, key=lambda x: x[1], reverse=True)
        with suppress(IndexError):
            reference_event, reference_date = event_dates[0]
            derived_event.date.start = copy(reference_date)
            _update_event(reference_event, derived_event)
            derived = True

    if derived:
        # @todo This needs to ONLY add events that are NEWLY derived/created, **AND** have actually been updated.
        # @todo because if a new event is created, but there were no existing events to update it from, we must not add a presence for it.
        if isinstance(derived_event, DerivedEvent):
            Presence(person, Subject(), derived_event)


def _event_is_complete() -> bool:
    if isinstance(derived_event.date, DateRange):
        if (not event_type.comes_before() or event_type.comes_before() and derived_event.date.end) and (
                not event_type.comes_after() or event_type.comes_after() and derived_event.date.start is not None):
            return False


def _get_primary_events(person: Person, event_type: Type[EventType]) -> Iterable[Event]:
    for presence in person.presences:
        if isinstance(presence.role, Subject):
            if isinstance(presence.event.type, event_type):
                yield presence.event


def _get_event_dates(person: Person, dependent_event_types: Set[Type[EventType]]) -> Iterable[Tuple[Event, Datey]]:
    for event in [presence.event for presence in person.presences]:
        # We cannot reliably determine dates based on reference events with calculated date ranges, as those events
        # would start or end *sometime* during the date range, but to derive dates we need reference events' exact
        # start and end dates.
        if isinstance(event, DerivedEvent):
            continue
        if not isinstance(event.type, tuple(dependent_event_types)):
            continue
        if isinstance(event.date, DateRange):
            if event.date.start is not None and event.date.start.comparable:
                yield event, event.date.start
            if event.date.end is not None and event.date.end.comparable:
                yield event, event.date.end
        elif event.date is not None and event.date.comparable:
            yield event, event.date


def _update_event(reference: Event, target: Event) -> None:
    target.citations.append(*reference.citations)
