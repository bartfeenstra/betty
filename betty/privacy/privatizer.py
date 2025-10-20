"""
Provide an API to determine if information should be kept private.
"""

from __future__ import annotations

from contextlib import suppress
from datetime import datetime
from typing import TYPE_CHECKING, Any, TypeAlias

from betty.ancestry.event import Event
from betty.ancestry.event_type.event_types import Death
from betty.ancestry.has_citations import HasCitations
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_notes import HasNotes
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Subject
from betty.ancestry.source import Source
from betty.date import Date, DateRange
from betty.locale.localizable import _
from betty.model import Entity
from betty.privacy import HasPrivacy, Privacy

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSequence

    from betty.user import User


_Expirable: TypeAlias = Person | Event | Date | None


class Privatizer:
    """
    Privatize resources.
    """

    def __init__(self, lifetime_threshold: int, *, user: User):
        self._lifetime_threshold = lifetime_threshold
        self._user = user
        self._seen: MutableSequence[HasPrivacy] = []

    async def privatize(self, subject: HasPrivacy) -> None:
        """
        Privatize a resource.
        """
        if subject.privacy is Privacy.PUBLIC:
            return

        if isinstance(subject, Person):
            await self._determine_person_privacy(subject)

        if isinstance(subject, Place):
            await self._determine_place_privacy(subject)

        if subject.privacy is not Privacy.PRIVATE:
            return

        if subject in self._seen:
            return
        self._seen.append(subject)

        if isinstance(subject, Person):
            await self._privatize_person(subject)

        if isinstance(subject, Presence):
            await self._privatize_presence(subject)

        if isinstance(subject, Event):
            await self._privatize_event(subject)

        if isinstance(subject, Place):
            await self._privatize_place(subject)

        if isinstance(subject, Source):
            await self._privatize_source(subject)

        if isinstance(subject, HasCitations):
            await self._privatize_has_citations(subject)

        if isinstance(subject, HasFileReferences):
            await self._privatize_has_file_references(subject)

        if isinstance(subject, HasNotes):
            await self._privatize_has_notes(subject)

    async def _privatize_person(self, person: Person) -> None:
        if not person.private:
            return

        for person_name in person.names:
            await self._mark_private(person_name, person)
            await self.privatize(person_name)
        for presence in person.presences:
            await self._mark_private(presence, person)
            await self.privatize(presence)

    async def _privatize_presence(self, presence: Presence) -> None:
        if not presence.private:
            return

        if isinstance(presence.role, Subject):
            await self._mark_private(presence.event, presence)
            await self.privatize(presence.event)
        await self._mark_private(presence.person, presence)
        await self.privatize(presence.person)

    async def _privatize_event(self, event: Event) -> None:
        if not event.private:
            return

        for presence in event.presences:
            await self._mark_private(presence, event)
            await self.privatize(presence)
        if event.place:
            await self.privatize(event.place)

    async def _privatize_place(self, place: Place) -> None:
        if not place.private:
            return

        for enclosure in place.enclosees:
            await self._mark_private(enclosure.enclosee, place)
            await self.privatize(enclosure.enclosee)
        for enclosure in place.enclosers:
            await self.privatize(enclosure.encloser)

    async def _privatize_has_citations(
        self, has_citations: HasCitations & HasPrivacy
    ) -> None:
        if not has_citations.private:
            return

        for citation in has_citations.citations:
            await self._mark_private(citation, has_citations)
            await self.privatize(citation)

    async def _privatize_source(self, source: Source) -> None:
        if not source.private:
            return

        for contained_source in source.contains:
            await self._mark_private(contained_source, source)
            await self.privatize(contained_source)
        for citation in source.citations:
            await self._mark_private(citation, source)
            await self.privatize(citation)

    async def _privatize_has_file_references(
        self, has_file_references: HasFileReferences & HasPrivacy
    ) -> None:
        if not has_file_references.private:
            return

        for file_reference in has_file_references.file_references:
            await self._mark_private(file_reference.file, has_file_references)
            await self.privatize(file_reference.file)

    async def _privatize_has_notes(self, has_notes: HasNotes & HasPrivacy) -> None:
        if not has_notes.private:
            return

        for note in has_notes.notes:
            await self._mark_private(note, has_notes)
            await self.privatize(note)

    def _ancestors_by_generation(
        self, person: Person, generations_ago: int = 1
    ) -> Iterator[tuple[Person, int]]:
        for parent in person.parents:
            yield parent, generations_ago
            yield from self._ancestors_by_generation(parent, generations_ago + 1)

    async def _determine_person_privacy(self, person: Person) -> None:
        # Do not change existing explicit privacy declarations.
        if person.privacy is not Privacy.UNDETERMINED:
            return

        # A dead person is not private, regardless of when they died.
        for presence in person.presences:
            if (
                presence.event.event_type.plugin.id == Death.plugin.id
                or presence.event.event_type.plugin.indicates == Death.plugin.id
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
        for descendant in person.descendants:
            if self.has_expired(descendant, 1):
                person.public = True
                return

        person.private = True
        await self._user.message_debug(
            _(
                "Privatized person {privatized_person_id} ({privatized_person}) because they are likely still alive."
            ).format(
                privatized_person_id=person.id,
                privatized_person=person.label,
            )
        )

    async def _determine_place_privacy(self, place: Place) -> None:
        # Do not change existing explicit privacy declarations.
        if place.privacy is not Privacy.UNDETERMINED:
            return

        # If there are non-private events, we will not privatize the place.
        for event in place.events:
            if not event.private:
                return

        # If there are non-private enclosed places, we will not privatize the place.
        for enclosure in place.enclosees:
            if not enclosure.enclosee.private:
                return

        place.private = True
        await self._user.message_debug(
            _(
                "Privatized place {privatized_place_id} ({privatized_place}) because it is not associated with any public information."
            ).format(
                privatized_place_id=place.id,
                privatized_place=place.label,
            )
        )

    def has_expired(
        self,
        subject: _Expirable,
        generations_ago: int = 0,
    ) -> bool:
        """
        Check if a subject of the given generation has expired.
        """
        if isinstance(subject, Person):
            return self._person_has_expired(subject, generations_ago)

        if isinstance(subject, Event):
            return self._event_has_expired(subject, generations_ago)

        if isinstance(subject, Date):
            return self._date_has_expired(subject, generations_ago)

        return False

    def _person_has_expired(self, person: Person, generations_ago: int) -> bool:
        for presence in person.presences:
            if self._event_has_expired(presence.event, generations_ago):
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

    async def _mark_private(self, target: HasPrivacy, reason: Any) -> None:
        # Do not change existing explicit privacy declarations.
        if target.own_privacy is not Privacy.UNDETERMINED:
            return

        target.private = True
        with suppress(ValueError):
            self._seen.remove(target)

        if isinstance(target, Entity) and isinstance(reason, Entity):
            await self._user.message_debug(
                _(
                    "Privatized {privatized_entity_type} {privatized_entity_id} ({privatized_entity}) because of {reason_entity_type} {reason_entity_id} ({reason_entity})."
                ).format(
                    privatized_entity_type=target.plugin.label,
                    privatized_entity_id=target.id,
                    privatized_entity=target.label,
                    reason_entity_type=reason.plugin.label,
                    reason_entity_id=reason.id,
                    reason_entity=reason.label,
                )
            )
