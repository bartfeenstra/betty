from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterator

from betty.app.extension import UserFacingExtension
from betty.functools import walk
from betty.load import PostLoader
from betty.locale import DateRange, Date, Localizer
from betty.model import Entity
from betty.model.ancestry import Person, Event, Citation, Source, HasPrivacy, Subject, File, HasFiles, HasCitations


class Privatizer(UserFacingExtension, PostLoader):
    async def post_load(self) -> None:
        self.privatize()

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Privatizer')

    @classmethod
    def description(cls, localizer: Localizer) -> str:
        return localizer._('Determine if people can be proven to have died. If not, mark them and their related resources private, but only if they are not already explicitly marked public or private. Enable the Anonymizer and Cleaner as well to make this most effective.')

    def privatize(self) -> None:
        seen: list[Entity] = []

        privatized = 0
        for person in self._app.project.ancestry.entities[Person]:
            private = person.private
            self._privatize_person(person, seen)
            if private is None and person.private is True:
                privatized += 1
        logger = logging.getLogger()
        logger.info(self._app.localizer._('Privatized {count} people because they are likely still alive.').format(count=privatized))

        for citation in self._app.project.ancestry.entities[Citation]:
            self._privatize_citation(citation, seen)

        for source in self._app.project.ancestry.entities[Source]:
            self._privatize_source(source, seen)

        for event in self._app.project.ancestry.entities[Event]:
            self._privatize_event(event, seen)

        for file in self._app.project.ancestry.entities[File]:
            self._privatize_file(file, seen)

    def _mark_private(self, has_privacy: HasPrivacy) -> None:
        # Do not change existing explicit privacy declarations.
        if has_privacy.private is None:
            has_privacy.private = True

    def _privatize_person(self, person: Person, seen: list[Entity]) -> None:
        # Do not change existing explicit privacy declarations.
        if person.private is None:
            person.private = self._person_is_private(person)

        if not person.private:
            return

        for presence in person.presences:
            if isinstance(presence.role, Subject) and presence.event is not None:
                self._mark_private(presence.event)
                self._privatize_event(presence.event, seen)

        self._privatize_has_citations(person, seen)
        self._privatize_has_files(person, seen)

    def _privatize_event(self, event: Event, seen: list[Entity]) -> None:
        if not event.private:
            return

        if event in seen:
            return
        seen.append(event)

        self._privatize_has_citations(event, seen)
        self._privatize_has_files(event, seen)

    def _privatize_has_citations(self, has_citations: HasCitations, seen: list[Entity]) -> None:
        for citation in has_citations.citations:
            self._mark_private(citation)
            self._privatize_citation(citation, seen)

    def _privatize_citation(self, citation: Citation, seen: list[Entity]) -> None:
        if not citation.private:
            return

        if citation in seen:
            return
        seen.append(citation)

        if citation.source is not None:
            self._mark_private(citation.source)
            self._privatize_source(citation.source, seen)
        self._privatize_has_files(citation, seen)

    def _privatize_source(self, source: Source, seen: list[Entity]) -> None:
        if not source.private:
            return

        if source in seen:
            return
        seen.append(source)

        self._privatize_has_files(source, seen)

    def _privatize_has_files(self, has_files: HasFiles, seen: list[Entity]) -> None:
        for file in has_files.files:
            self._mark_private(file)
            self._privatize_file(file, seen)

    def _privatize_file(self, file: File, seen: list[Entity]) -> None:
        if not file.private:
            return

        if file in seen:
            return
        seen.append(file)

        self._privatize_has_citations(file, seen)

    def _person_is_private(self, person: Person) -> bool:
        # A dead person is not private, regardless of when they died.
        if person.end is not None:
            if person.end.date is None:
                return False
            if self._event_has_expired(person.end, 0):
                return False

        if self._person_has_expired(person, 1):
            return False

        def ancestors(person: Person, generation: int = -1) -> Iterator[tuple[int, Person]]:
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
            if presence.event is not None and self._event_has_expired(presence.event, multiplier):
                return True
        return False

    def _event_has_expired(self, event: Event, multiplier: int) -> bool:
        assert multiplier >= 0

        date = event.date

        if isinstance(date, DateRange):
            # We can only determine event expiration with certainty if we have an end date to work with. Someone born in
            # 2000 can have a valid birth event with a start date of 1800, which does nothing to help us determine
            # expiration.
            date = date.end

        return self._date_has_expired(date, multiplier)

    def _date_has_expired(self, date: Date | None, multiplier: int) -> bool:
        assert multiplier >= 0

        if date is None:
            return False

        if not date.comparable:
            return False

        return date <= Date(datetime.now().year - self._app.project.configuration.lifetime_threshold * multiplier, datetime.now().month, datetime.now().day)
