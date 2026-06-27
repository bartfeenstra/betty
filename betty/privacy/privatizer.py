"""
The privatizer API.
"""

from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, final

from betty import default_lifetime_threshold
from betty.date import Date, DateRange
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entity import Entity
from betty.event_types.death import Death
from betty.localizables.gettext import _
from betty.privacy import Privacy

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSet

    from betty.entities.event import Event
    from betty.user import User


@final
class Privatizer:
    """
    Privatize entities.
    """

    def __init__(
        self, *, lifetime_threshold: int = default_lifetime_threshold, user: User
    ):
        self._lifetime_threshold = lifetime_threshold
        self._user = user

    async def privatize(self, *entities: Entity) -> None:
        """
        Privatize entities.
        """
        seen = set()
        for entity in entities:
            await self._privatize(entity, seen)

    async def _privatize(self, entity: Entity, seen: MutableSet[Entity], /) -> None:
        if entity.privacy is Privacy.PUBLIC:
            return

        if isinstance(entity, Person):
            await self._determine_person_privacy(entity)

        if isinstance(entity, Place):
            await self._determine_place_privacy(entity)

        if entity.privacy is not Privacy.PRIVATE:
            return

        if entity in seen:
            return
        seen.add(entity)

        if entity.privacy.publishable:
            return

        for association in entity.associations():
            for associate in association.get_associates(entity):
                if association.privatize(entity, associate):
                    await self._mark_private(associate, entity, seen)
                    await self.privatize(associate)

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
            if presence.event.event_type.plugin().id == Death.plugin().id:
                if presence.event.date is None:
                    person.privacy = Privacy.PUBLIC
                    return
                if self._event_has_expired(presence.event, 0):
                    person.privacy = Privacy.PUBLIC
                    return

        if self.person_has_expired(person, 1):
            person.privacy = Privacy.PUBLIC
            return

        for ancestor, generations_ago in self._ancestors_by_generation(person):
            if self.person_has_expired(ancestor, generations_ago + 1):
                person.privacy = Privacy.PUBLIC
                return

        # If any descendant has any expired event, the person is considered not private.
        for descendant in person.descendants:
            if self.person_has_expired(descendant, 1):
                person.privacy = Privacy.PUBLIC
                return

        person.privacy = Privacy.PRIVATE
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

        # If there are publishable events, we will not privatize the place.
        for event in place.events:
            if event.privacy.publishable:
                return

        # If there are publishable enclosed places, we will not privatize the place.
        for enclosure in place.enclosees:
            if enclosure.enclosee.privacy.publishable:
                return

        place.privacy = Privacy.PRIVATE
        await self._user.message_debug(
            _(
                "Privatized place {privatized_place_id} ({privatized_place}) because it is not associated with any public information."
            ).format(
                privatized_place_id=place.id,
                privatized_place=place.label,
            )
        )

    @final
    def person_has_expired(self, person: Person, generations_ago: int, /) -> bool:
        """
        Check if a person has expired.
        """
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

        if date is None:
            return False
        return self._date_has_expired(date, generations_ago)

    def _date_has_expired(
        self,
        date: Date,
        generations_ago: int,
    ) -> bool:
        if not date.comparable:
            return False

        # @todo Add some caching?
        # @todo Also, is this the moment where we split the lifetime threshold into upper and lower constraints?
        # @todo We don't have to make the lower one configurable (yet...)
        # @todo
        # @todo
        # @todo
        return date <= Date(
            datetime.now(tz=UTC).year - self._lifetime_threshold * generations_ago,
            datetime.now(tz=UTC).month,
            datetime.now(tz=UTC).day,
        )

    async def _mark_private(
        self,
        target: Entity,
        reason: Any,
        seen: MutableSet[Entity],
    ) -> None:
        # Do not change existing explicit privacy declarations.
        if target.privacy is not Privacy.UNDETERMINED:
            return

        target.privacy = Privacy.PRIVATE
        with suppress(ValueError):
            seen.remove(target)

        if isinstance(target, Entity) and isinstance(reason, Entity):
            await self._user.message_debug(
                _(
                    "Privatized {privatized_entity_type} {privatized_entity_id} ({privatized_entity}) because of {reason_entity_type} {reason_entity_id} ({reason_entity})."
                ).format(
                    privatized_entity_type=target.plugin().label,
                    privatized_entity_id=target.id,
                    privatized_entity=target.label,
                    reason_entity_type=reason.plugin().label,
                    reason_entity_id=reason.id,
                    reason_entity=reason.label,
                )
            )
