from datetime import datetime
from typing import List, Tuple, Callable, Optional

from betty.ancestry import Ancestry, Person, Event
from betty.parse import PostParseEvent
from betty.plugin import Plugin


class Privatizer(Plugin):
    def __init__(self):
        self._threshold = 100

    def subscribes_to(self) -> List[Tuple[str, Callable]]:
        return (
            (PostParseEvent, lambda event: self.privatize(event.ancestry)),
        )

    def privatize(self, ancestry: Ancestry) -> None:
        for person in ancestry.people.values():
            self._privatize_person(person)

    def _privatize_person(self, person: Person) -> None:
        if person.private is not None:
            return

        person.private = self._person_is_private(person)

    def _person_is_private(self, person: Person) -> bool:
        if person.death is not None:
            return False

        if self._birth_has_expired(person, 0):
            return False

        def ancestors(person: Person, generation: int):
            for parent in person.parents:
                yield generation, parent
                yield from ancestors(parent, generation - 1)

        for generation, ancestor in ancestors(person, 0):
            if self._birth_has_expired(ancestor, generation):
                return False
            if self._death_has_expired(ancestor, generation):
                return False

        def descendants(person: Person, generation: int):
            for child in person.children:
                yield generation, child
                yield from descendants(child, generation + 1)

        for generation, descendant in descendants(person, 0):
            if self._birth_has_expired(descendant, generation):
                return False
            if self._death_has_expired(descendant, generation):
                return False

        return True

    def _birth_has_expired(self, person: Person, generation: int) -> bool:
        return self._event_has_expired(person.birth, abs(generation) + 1)

    def _death_has_expired(self, person: Person, generation: int) -> bool:
        return self._event_has_expired(person.death, abs(generation))

    def _event_has_expired(self, event: Optional[Event], multiplier: int) -> bool:
        if event is None:
            return False

        if event.date is None:
            return False

        if event.date.year is None:
            return False

        return event.date.year + self._threshold * multiplier < datetime.now().year
