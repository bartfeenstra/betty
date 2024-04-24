"""
Provide an API to determine if information should be kept private.
"""

from __future__ import annotations

import logging
from contextlib import suppress
from datetime import datetime
from typing import Iterator, TypeAlias, Any

from betty.functools import walk
from betty.locale import DateRange, Date, Localizer
from betty.model import Entity
from betty.model.ancestry import (
    Person,
    Event,
    HasFiles,
    HasCitations,
    HasNotes,
    Source,
    Presence,
    Privacy,
    HasPrivacy,
    Subject,
    Place,
)
from betty.model.event_type import EndOfLifeEventType

Expirable: TypeAlias = Person | Event | Date | None


class Privatizer:
    def __init__(
        self,
        lifetime_threshold: int,
        *,
        localizer: Localizer,
    ):
        self._lifetime_threshold = lifetime_threshold
        self._localizer = localizer
        self._seen: list[HasPrivacy] = []

    def privatize(self, subject: HasPrivacy) -> None:
        if subject.privacy is Privacy.PUBLIC:
            return

        if isinstance(subject, Person):
            self._determine_person_privacy(subject)

        if isinstance(subject, Place):
            self._determine_place_privacy(subject)

        if subject.privacy is not Privacy.PRIVATE:
            return

        if subject in self._seen:
            return
        self._seen.append(subject)

        if isinstance(subject, Person):
            self._privatize_person(subject)

        if isinstance(subject, Presence):
            self._privatize_presence(subject)

        if isinstance(subject, Event):
            self._privatize_event(subject)

        if isinstance(subject, Place):
            self._privatize_place(subject)

        if isinstance(subject, Source):
            self._privatize_source(subject)

        if isinstance(subject, HasCitations):
            self._privatize_has_citations(subject)

        if isinstance(subject, HasFiles):
            self._privatize_has_files(subject)

        if isinstance(subject, HasNotes):
            self._privatize_has_notes(subject)

    def _privatize_person(self, person: Person) -> None:
        if not person.private:
            return

        for person_name in person.names:
            self._mark_private(person_name, person)
            self.privatize(person_name)
        for presence in person.presences:
            self._mark_private(presence, person)
            self.privatize(presence)

    def _privatize_presence(self, presence: Presence) -> None:
        if not presence.private:
            return

        if presence.event is not None and isinstance(presence.role, Subject):
            self._mark_private(presence.event, presence)
            self.privatize(presence.event)
        if presence.person is not None:
            self._mark_private(presence.person, presence)
            self.privatize(presence.person)

    def _privatize_event(self, event: Event) -> None:
        if not event.private:
            return

        for presence in event.presences:
            self._mark_private(presence, event)
            self.privatize(presence)
        if event.place:
            self.privatize(event.place)

    def _privatize_place(self, place: Place) -> None:
        if not place.private:
            return

        for enclosure in place.encloses:
            if not enclosure.encloses:
                continue
            self._mark_private(enclosure.encloses, place)
            self.privatize(enclosure.encloses)
        for enclosure in place.enclosed_by:
            if not enclosure.enclosed_by:
                continue
            self.privatize(enclosure.enclosed_by)

    def _privatize_has_citations(
        self, has_citations: HasCitations & HasPrivacy
    ) -> None:
        if not has_citations.private:
            return

        for citation in has_citations.citations:
            self._mark_private(citation, has_citations)
            self.privatize(citation)

    def _privatize_source(self, source: Source) -> None:
        if not source.private:
            return

        for contained_source in source.contains:
            self._mark_private(contained_source, source)
            self.privatize(contained_source)
        for citation in source.citations:
            self._mark_private(citation, source)
            self.privatize(citation)

    def _privatize_has_files(self, has_files: HasFiles & HasPrivacy) -> None:
        if not has_files.private:
            return

        for file in has_files.files:
            self._mark_private(file, has_files)
            self.privatize(file)

    def _privatize_has_notes(self, has_notes: HasNotes & HasPrivacy) -> None:
        if not has_notes.private:
            return

        for note in has_notes.notes:
            self._mark_private(note, has_notes)
            self.privatize(note)

    def _ancestors_by_generation(
        self, person: Person, generations_ago: int = 1
    ) -> Iterator[tuple[Person, int]]:
        for parent in person.parents:
            yield parent, generations_ago
            yield from self._ancestors_by_generation(parent, generations_ago + 1)

    def _determine_person_privacy(self, person: Person) -> None:
        # Do not change existing explicit privacy declarations.
        if person.privacy is not Privacy.UNDETERMINED:
            return

        # A dead person is not private, regardless of when they died.
        for presence in person.presences:
            if presence.event and issubclass(
                presence.event.event_type, EndOfLifeEventType
            ):
                if presence.event.date is None:
                    person.public = True
                    return
                if self.has_expired(presence.event, 0):
                    person.public = True
                    return

        if self.has_expired(person, 1):
            person.public = True
            return

        for ancestor, generations_ago in self._ancestors_by_generation(person):
            if self.has_expired(ancestor, generations_ago + 1):
                person.public = True
                return

        # If any descendant has any expired event, the person is considered not private.
        for descendant in walk(person, "children"):
            if self.has_expired(descendant, 1):
                person.public = True
                return

        person.private = True
        logging.getLogger(__name__).debug(
            self._localizer._(
                "Privatized person {privatized_person_id} ({privatized_person}) because they are likely still alive."
            ).format(
                privatized_person_id=person.id,
                privatized_person=person.label.localize(self._localizer),
            )
        )

    def _determine_place_privacy(self, place: Place) -> None:
        # Do not change existing explicit privacy declarations.
        if place.privacy is not Privacy.UNDETERMINED:
            return

        # If there are non-private events, we will not privatize the place.
        for event in place.events:
            if not event.private:
                return

        # If there are non-private enclosed places, we will not privatize the place.
        for enclosure in place.encloses:
            if not enclosure.encloses:
                continue
            if not enclosure.encloses.private:
                return

        place.private = True
        logging.getLogger(__name__).debug(
            self._localizer._(
                "Privatized place {privatized_place_id} ({privatized_place}) because it is not associated with any public information."
            ).format(
                privatized_place_id=place.id,
                privatized_place=place.label.localize(self._localizer),
            )
        )

    def has_expired(
        self,
        subject: Expirable,
        generations_ago: int = 0,
    ) -> bool:
        if isinstance(subject, Person):
            return self._person_has_expired(subject, generations_ago)

        if isinstance(subject, Event):
            return self._event_has_expired(subject, generations_ago)

        if isinstance(subject, Date):
            return self._date_has_expired(subject, generations_ago)

        return False

    def _person_has_expired(self, person: Person, generations_ago: int) -> bool:
        for presence in person.presences:
            if presence.event is not None and self._event_has_expired(
                presence.event, generations_ago
            ):
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

        return date <= Date(
            datetime.now().year - self._lifetime_threshold * generations_ago,
            datetime.now().month,
            datetime.now().day,
        )

    def _mark_private(self, target: HasPrivacy, reason: Any) -> None:
        # Do not change existing explicit privacy declarations.
        if target.own_privacy is not Privacy.UNDETERMINED:
            return

        target.private = True
        with suppress(ValueError):
            self._seen.remove(target)

        if isinstance(target, Entity) and isinstance(reason, Entity):
            logging.getLogger(__name__).debug(
                self._localizer._(
                    "Privatized {privatized_entity_type} {privatized_entity_id} ({privatized_entity}) because of {reason_entity_type} {reason_entity_id} ({reason_entity})."
                ).format(
                    privatized_entity_type=target.entity_type_label().localize(
                        self._localizer
                    ),
                    privatized_entity_id=target.id,
                    privatized_entity=target.label.localize(self._localizer),
                    reason_entity_type=reason.entity_type_label().localize(
                        self._localizer
                    ),
                    reason_entity_id=reason.id,
                    reason_entity=reason.label.localize(self._localizer),
                )
            )
