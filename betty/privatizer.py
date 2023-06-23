from __future__ import annotations

from datetime import datetime
from typing import Iterator

from typing_extensions import TypeAlias

from betty.functools import walk
from betty.locale import DateRange, Date
from betty.model.ancestry import Person, Event, Citation, HasPrivacy, Subject, HasFiles, HasCitations


Expirable: TypeAlias = 'Person | Event | Date | None'


class Privatizer:
    def __init__(self, lifetime_threshold: int):
        self._lifetime_threshold = lifetime_threshold
        self._seen: list[HasPrivacy] = []

    def privatize(self, subject: HasPrivacy) -> None:
        self._seen.clear()
        self._privatize(subject)

    def _privatize(self, subject: HasPrivacy) -> None:
        print(subject)
        print(subject)
        print(subject)
        print(subject)
        print(subject.private)
        print(subject.private)
        print(subject.private)
        if subject.private is False:
            return

        if subject in self._seen:
            return
        self._seen.append(subject)

        if isinstance(subject, Person):
            self._privatize_person(subject)

        if isinstance(subject, Citation):
            self._privatize_citation(subject)

        if isinstance(subject, HasCitations):
            self._privatize_has_citations(subject)

        if isinstance(subject, HasFiles):
            self._privatize_has_files(subject)

        # Do not change existing explicit privacy declarations.
        if subject.private is None:
            subject.private = True

    def _privatize_person(self, person: Person) -> None:
        # Do not change existing explicit privacy declarations.
        if person.private is None:
            person.private = self._is_person_private(person)
            if not person.private:
                return

        for presence in person.presences:
            if isinstance(presence.role, Subject) and presence.event is not None:
                self._privatize(presence.event)

    def _privatize_has_citations(self, has_citations: HasCitations) -> None:
        for citation in has_citations.citations:
            self._privatize(citation)

    def _privatize_citation(self, citation: Citation) -> None:
        if citation.source is not None:
            self._privatize(citation.source)

    def _privatize_has_files(self, has_files: HasFiles) -> None:
        for file in has_files.files:
            self._privatize(file)

    def _ancestors_by_generation(self, person: Person, generations_ago: int = 1) -> Iterator[tuple[Person, int]]:
        for parent in person.parents:
            yield parent, generations_ago
            yield from self._ancestors_by_generation(parent, generations_ago + 1)

    def _is_person_private(self, person: Person) -> bool:
        # A dead person is not private, regardless of when they died.
        if person.end is not None:
            if person.end.date is None:
                return False
            if self.has_expired(person.end, 0):
                return False

        if self.has_expired(person, 1):
            return False

        for ancestor, generations_ago in self._ancestors_by_generation(person):
            if self.has_expired(ancestor, generations_ago + 1):
                return False

        # If any descendant has any expired event, the person is considered not private.
        for descendant in walk(person, 'children'):
            if self.has_expired(descendant, 1):
                return False

        return True

    def has_expired(
        self,
        subject: Expirable,
        generations_ago: int = 0,
    ) -> bool:
        if subject is None:
            return False

        if isinstance(subject, Person):
            return self._person_has_expired(subject, generations_ago)

        if isinstance(subject, Event):
            return self._event_has_expired(subject, generations_ago)

        if isinstance(subject, Date):
            return self._date_has_expired(subject, generations_ago)

        return False

    def _person_has_expired(self, person: Person, generations_ago: int) -> bool:
        for presence in person.presences:
            if presence.event is not None and self._event_has_expired(presence.event, generations_ago):
                return True
        return False

    def _event_has_expired(self, event: Event, generations_ago: int) -> bool:
        date = event.date

        if isinstance(date, DateRange):
            # We can only determine event expiration with certainty if we have an end date to work with. Someone born in
            # 2000 can have a valid birth event with a start date of 1800, which does nothing to help us determine
            # expiration.
            date = date.end

        return self.has_expired(date, generations_ago)

    def _date_has_expired(
        self,
        date: Date,
        generations_ago: int,
    ) -> bool:
        if not date.comparable:
            return False

        return date <= Date(datetime.now().year - self._lifetime_threshold * generations_ago, datetime.now().month, datetime.now().day)
