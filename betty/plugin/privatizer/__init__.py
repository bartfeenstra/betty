import logging
from datetime import datetime
from typing import Any, Optional

from betty.ancestry import Ancestry, Person, Event, Citation, Source, HasPrivacy, Subject
from betty.functools import walk
from betty.locale import DateRange, Date
from betty.parse import PostParser
from betty.plugin import Plugin, NO_CONFIGURATION
from betty.site import Site


class Privatizer(Plugin, PostParser):
    def __init__(self, ancestry: Ancestry, lifetime_threshold: int):
        self._ancestry = ancestry
        self._lifetime_threshold = lifetime_threshold

    @classmethod
    def for_site(cls, site: Site, configuration: Any = NO_CONFIGURATION):
        return cls(site.ancestry, site.configuration.lifetime_threshold)

    async def post_parse(self) -> None:
        self.privatize(self._ancestry)

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


def privatize_person(person: Person, lifetime_threshold: int) -> None:
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
    if person.end is not None:
        if person.end.date is None:
            return False
        if _event_has_expired(person.end, lifetime_threshold, 0):
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

    date = event.date

    if isinstance(date, DateRange):
        # We can only determine event expiration with certainty if we have an end date to work with. Someone born in
        # 2000 can have a valid birth event with a start date of 1800, which does nothing to help us determine
        # expiration.
        date = date.end

    return _date_has_expired(date, lifetime_threshold, multiplier)


def _date_has_expired(date: Optional[Date], lifetime_threshold: int, multiplier: int) -> bool:
    assert multiplier >= 0

    if date is None:
        return False

    if not date.comparable:
        return False

    return date <= Date(datetime.now().year - lifetime_threshold * multiplier, datetime.now().month, datetime.now().day)
