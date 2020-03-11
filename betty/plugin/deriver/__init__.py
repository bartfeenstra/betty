import logging
from collections import defaultdict
from copy import copy
from typing import List, Tuple, Callable, Optional, Dict, Set, Type

from betty.ancestry import Ancestry, Person, Presence, Event
from betty.event import Event as DispatchedEvent
from betty.locale import DateRange
from betty.parse import PostParseEvent
from betty.plugin import Plugin
from betty.plugin.cleaner import Cleaner


class DerivedEvent(Event):
    pass


class Deriver(Plugin):
    def subscribes_to(self) -> List[Tuple[Type[DispatchedEvent], Callable]]:
        return [
            (PostParseEvent, lambda event: derive(event.ancestry)),
        ]

    @classmethod
    def comes_after(cls) -> Set[Type[Plugin]]:
        return {Cleaner}


def derive(ancestry: Ancestry) -> None:
    derivations = defaultdict(lambda: 0)
    try:
        for person in ancestry.people.values():
            _derive_person(person, derivations)
    finally:
        logger = logging.getLogger()
        logger.info('Created %d additional births derived from existing information.' % derivations[Event.Type.BIRTH])
        logger.info('Created %d additional deaths derived from existing information.' % derivations[Event.Type.DEATH])


def _derive_person(person: Person, derivations: Dict) -> None:
    _derive_event(person, Event.Type.BIRTH, False, derivations)
    _derive_event(person, Event.Type.DEATH, True, derivations)


def _derive_event(person: Person, event_type: Event.Type, after: bool, derivations: Dict) -> None:
    derived_event = _get_primary_event(person, event_type)
    if derived_event is None:
        derived_event = DerivedEvent(event_type, DateRange())
    elif isinstance(derived_event.date, DateRange):
        if after and derived_event.date.start is not None:
            return
        if not after and derived_event.date.end is not None:
            return
    elif derived_event.date is None:
        derived_event.date = DateRange()
    else:
        return

    event_dates = []
    for event in [presence.event for presence in person.presences if presence.event.type != event_type]:
        if isinstance(event.date, DateRange):
            if event.date.start is not None and event.date.start.comparable:
                event_dates.append((event, event.date.start))
            if event.date.end is not None and event.date.end.comparable:
                event_dates.append((event, event.date.end))
        elif event.date is not None and event.date.comparable:
            event_dates.append((event, event.date))
    event_dates = sorted(event_dates, key=lambda x: x[1], reverse=after)
    try:
        threshold_event, threshold_date = event_dates[0]
    except IndexError:
        return
    if after:
        derived_event.date.start = copy(threshold_date)
    else:
        derived_event.date.end = copy(threshold_date)
    for citation in threshold_event.citations:
        derived_event.citations.append(citation)
    if isinstance(derived_event, DerivedEvent):
        Presence(person, Presence.Role.SUBJECT, derived_event)

    derivations[event_type] += 1


def _get_primary_event(person: Person, event_type: Event.Type) -> Optional[Event]:
    for presence in person.presences:
        if presence.role == Presence.Role.SUBJECT:
            if presence.event.type == event_type:
                return presence.event
