import logging
from datetime import datetime
from typing import List, Tuple, Callable, Type

from betty.ancestry import Ancestry, Person, Event, Citation, Source, Presence, HasPrivacy
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
            (PostParseEvent, lambda event: self.privatize(event.ancestry)),
        ]

    def privatize(self, ancestry: Ancestry) -> None:
        privatized = 0
        for person in ancestry.people.values():
            private = person.private
            self._privatize_person(person)
            if private is None and person.private is True:
                privatized += 1
        logger = logging.getLogger()
        logger.info('Privatized %d people because they are likely still alive.' % privatized)

        for citation in ancestry.citations.values():
            self._privatize_citation(citation)

        for source in ancestry.sources.values():
            self._privatize_source(source)

    def _mark_private(self, has_privacy: HasPrivacy) -> None:
        # Do not change existing explicit privacy declarations.
        if has_privacy.private is None:
            has_privacy.private = True

    def _privatize_person(self, person: Person) -> None:
        # Do not change existing explicit privacy declarations.
        if person.private is None:
            person.private = self._person_is_private(person)

        if not person.private:
            return

        for presence in person.presences:
            if presence.role == Presence.Role.SUBJECT:
                presence.event.private = True
        for file in person.files:
            self._mark_private(file)
        for citation in person.citations:
            self._mark_private(citation)
            self._privatize_citation(citation)

    def _privatize_citation(self, citation: Citation) -> None:
        if not citation.private:
            return

        self._mark_private(citation.source)
        self._privatize_source(citation.source)
        for file in citation.files:
            self._mark_private(file)

    def _privatize_source(self, source: Source) -> None:
        if not source.private:
            return

        for file in source.files:
            self._mark_private(file)

    def _person_is_private(self, person: Person) -> bool:
        # A dead person is not private, regardless of when they died.
        if person.end is not None and self._event_has_expired(person.end, 0):
            return False

        if self._person_has_expired(person, 1):
            return False

        def ancestors(person: Person, generation: int = -1):
            for parent in person.parents:
                yield generation, parent
                yield from ancestors(parent, generation - 1)

        for generation, ancestor in ancestors(person):
            if self._person_has_expired(ancestor, abs(generation) + 1):
                return False

        # If any descendant has any expired event, the person is considered not private.
        for descendant in walk(person, 'children'):
            if self._person_has_expired(descendant, 1):
                return False

        return True

    def _person_has_expired(self, person: Person, multiplier: int) -> bool:
        for presence in person.presences:
            if self._event_has_expired(presence.event, multiplier):
                return True
        return False

    def _event_has_expired(self, event: Event, multiplier: int) -> bool:
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

        return date <= Date(datetime.now().year - self._lifetime_threshold * multiplier, datetime.now().month, datetime.now().day)
