"""
The privatizer API.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, final

from betty.entities.person import Person
from betty.event_types.death import Death
from betty.localizables.gettext import _
from betty.privacy import Privacy

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSet

    from betty.entity import Entity
    from betty.lifetime import Lifetime
    from betty.user import User


@final
class Privatizer:
    """
    Privatize entities.
    """

    def __init__(self, *, lifetime: Lifetime, user: User):
        self._lifetime = lifetime
        self._user = user

    async def privatize(self, *entities: Entity) -> None:
        """
        Privatize entities and their associates.
        """
        seen = set()
        for entity in entities:
            await self._privatize(entity, seen)

    async def _privatize(self, entity: Entity, seen: MutableSet[Entity], /) -> None:
        if entity in seen:
            return
        seen.add(entity)

        if not entity.privacy.determined and isinstance(entity, Person):
            await self._determine_person_privacy(entity)

        if entity.privacy is not Privacy.PRIVATE:
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
        for presence in person.presences:
            if presence.event.event_type.plugin().id == Death.plugin().id:
                person.privacy = Privacy.PUBLIC
                return

        if self._lifetime.is_expired(person):
            person.privacy = Privacy.PUBLIC
            return

        for ancestor, generations_ago in self._ancestors_by_generation(person):
            if self._lifetime.is_expired(ancestor, generations_ago + 1):
                person.privacy = Privacy.PUBLIC
                return

        # If any descendant has any expired event, the person is considered not private.
        for descendant in person.descendants:
            if self._lifetime.is_expired(descendant):
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

    async def _mark_private(
        self, owner: Entity, associate: Entity, seen: MutableSet[Entity]
    ) -> None:
        # Do not change existing explicit privacy declarations.
        if associate.privacy is not Privacy.UNDETERMINED:
            return

        associate.privacy = Privacy.PRIVATE
        with suppress(ValueError):
            seen.remove(associate)

        await self._user.message_debug(
            _(
                "Privatized {associate_type} {associate_id} ({associate}) because of {owner_type} {owner_id} ({owner})."
            ).format(
                associate_type=associate.plugin().label,
                associate_id=associate.id,
                associate=associate.label,
                owner_type=owner.plugin().label,
                owner_id=owner.id,
                owner=owner.label,
            )
        )
