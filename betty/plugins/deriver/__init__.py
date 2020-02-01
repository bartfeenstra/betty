import logging
from copy import copy
from typing import List, Tuple, Callable, Optional

from betty.ancestry import Ancestry, Person, Presence, Event
from betty.locale import Date, Period
from betty.parse import PostParseEvent
from betty.plugin import Plugin


class DerivedEvent(Event):
    pass


class Deriver(Plugin):
    def subscribes_to(self) -> List[Tuple[str, Callable]]:
        return (
            (PostParseEvent, lambda event: derive(event.ancestry)),
        )


class _Derivations:
    def __init__(self):
        self.births = 0
        self.deaths = 0


def derive(ancestry: Ancestry) -> None:
    derivations = _Derivations()
    for person in ancestry.people.values():
        _derive_person(person, derivations)
    logger = logging.getLogger()
    logger.info('Derived %d births from existing information.' % derivations.births)
    logger.info('Derived %d deaths from existing information.' % derivations.deaths)


def _derive_person(person: Person, derivations: _Derivations) -> None:
    _derive_birth(person, derivations)
    _derive_death(person, derivations)


def _derive_birth(person: Person, derivations: _Derivations) -> None:
    birth = _get_primary_event(person, Event.Type.BIRTH)
    if birth is None:
        birth = DerivedEvent(Event.Type.BIRTH)
    if birth.date is not None:
        return

    # Get the earliest possible date, accounting for events without dates, and events with periods.
    # @todo this goes wrong when we have a birth without a date, the sources of which are then added to itself....?
    event_dates = []
    for presence in person.presences:
        event = presence.event
        start_date = _get_start_date(presence.event)
        if start_date is not None and start_date.complete:
            event_dates.append((event, start_date))
    event_dates = sorted(event_dates, key=lambda x: x[1])
    try:
        earliest_event, earliest_date = event_dates[0]
    except IndexError:
        return
    birth.date = Period(None, copy(earliest_date))
    for citation in earliest_event.citations:
        birth.citations.append(citation)
    presence = Presence(Presence.Role.SUBJECT)
    presence.event = birth
    person.presences.append(presence)
    derivations.births += 1


def _derive_death(person: Person, derivations: _Derivations) -> None:
    death = _get_primary_event(person, Event.Type.DEATH)
    if death is None:
        death = DerivedEvent(Event.Type.DEATH)
    if death.date is not None:
        return

    # Get the earliest possible date, accounting for events without dates, and events with periods.
    event_dates = []
    for presence in person.presences:
        event = presence.event
        end_date = _get_end_date(presence.event)
        if end_date is not None and end_date.complete:
            event_dates.append((event, end_date))
    event_dates = sorted(event_dates, key=lambda x: x[1], reverse=True)
    try:
        latest_event, earliest_date = event_dates[0]
    except IndexError:
        return
    death.date = Period(copy(earliest_date))
    for citation in latest_event.citations:
        death.citations.append(citation)
    presence = Presence(Presence.Role.SUBJECT)
    presence.event = death
    person.presences.append(presence)
    derivations.deaths += 1


def _get_primary_event(person: Person, event_type: Event.Type) -> Optional[Event]:
    for presence in person.presences:
        if presence.role == Presence.Role.SUBJECT:
            event = presence.event
            if event.type == event_type:
                return event
    return None


def _get_start_date(event: Event) -> Optional[Date]:
    date = event.date
    if isinstance(date, Period):
        return date.start
    return date


def _get_end_date(event: Event) -> Optional[Date]:
    date = event.date
    if isinstance(date, Period):
        return date.end
    return date
