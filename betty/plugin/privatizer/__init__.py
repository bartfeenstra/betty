import logging
from datetime import datetime
from typing import List, Tuple, Callable, Type

from betty.ancestry import Ancestry, Person, Event, Citation, Source, HasPrivacy, Subject
from betty.event import Event as DispatchedEvent
from betty.functools import walk
from betty.locale import DateRange, Date
from betty.parse import PostParseEvent
from betty.plugin import Plugin


class Privatizer(Plugin):
    def __init__(self):
        self._lifetime_threshold = 100

    def subscribes_to(self) -> List[Tuple[Type[DispatchedEvent], Callable]]:
        return [
            (PostParseEvent, self._privatize),
        ]

    async def _privatize(self, event: PostParseEvent) -> None:
        self.privatize(event.ancestry)

    def privatize(self, ancestry: Ancestry) -> None:
        privatized = 0
        for person in ancestry.people.values():
            private = person.private
            privatize_person(person, self._lifetime_threshold)
            if private is None and person.private is True:
                privatized += 1
        logger = logging.getLogger()
        logger.info('Privatized %d people because they are likely still alive.' % privatized)

        for citation in ancestry.citations.values():
            privatize_citation(citation)

        for source in ancestry.sources.values():
            privatize_source(source)


def _mark_private(has_privacy: HasPrivacy) -> None:
    # Do not change existing explicit privacy declarations.
    if has_privacy.private is None:
        has_privacy.private = True


def privatize_person(person: Person, lifetime_threshold: int = 100) -> None:
    # Do not change existing explicit privacy declarations.
    if person.private is None:
        person.private = _person_is_private(person, lifetime_threshold)

    if not person.private:
        return

    for presence in person.presences:
        if isinstance(presence.role, Subject):
            _mark_private(presence.event)
            privatize_event(presence.event)
    for file in person.files:
        _mark_private(file)
    for citation in person.citations:
        _mark_private(citation)
        privatize_citation(citation)


def privatize_event(event: Event) -> None:
    if not event.private:
        return

    for file in event.files:
        _mark_private(file)
    for citation in event.citations:
        _mark_private(citation)
        privatize_citation(citation)


def privatize_citation(citation: Citation) -> None:
    if not citation.private:
        return

    _mark_private(citation.source)
    privatize_source(citation.source)
    for file in citation.files:
        _mark_private(file)


def privatize_source(source: Source) -> None:
    if not source.private:
        return

    for file in source.files:
        _mark_private(file)


def _person_is_private(person: Person, lifetime_threshold: int) -> bool:
    # A dead person is not private, regardless of when they died.
    if person.end is not None and _event_has_expired(person.end, lifetime_threshold, 0):
        return False

    if _person_has_expired(person, lifetime_threshold, 1):
        return False

    def ancestors(person: Person, generation: int = -1):
        for parent in person.parents:
            yield generation, parent
            yield from ancestors(parent, generation - 1)

    for generation, ancestor in ancestors(person):
        if _person_has_expired(ancestor, lifetime_threshold, abs(generation) + 1):
            return False

    # If any descendant has any expired event, the person is considered not private.
    for descendant in walk(person, 'children'):
        if _person_has_expired(descendant, lifetime_threshold, 1):
            return False

    return True


def _person_has_expired(person: Person, lifetime_threshold: int, multiplier: int) -> bool:
    for presence in person.presences:
        if _event_has_expired(presence.event, lifetime_threshold, multiplier):
            return True
    return False


def _event_has_expired(event: Event, lifetime_threshold: int, multiplier: int) -> bool:
    assert multiplier >= 0

    if event.date is None:
        return False

    date = event.date

    if isinstance(date, DateRange):
        if date.end is not None:
            date = date.end
        # A multiplier of 0 is only used for generation 0's end-of-life events. If those only have start dates, they
        # do not contain any information about by which date the event definitely has taken place, and therefore
        # they MUST be checked using another method call with a multiplier of 1 to verify they lie far enough in the
        # past.
        elif multiplier != 0:
            date = date.start
        else:
            return False

    if date is None:
        return False

    if not date.comparable:
        return False

    return date <= Date(datetime.now().year - lifetime_threshold * multiplier, datetime.now().month, datetime.now().day)
