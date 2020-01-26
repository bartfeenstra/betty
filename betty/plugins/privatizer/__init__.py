from datetime import datetime
from typing import List, Tuple, Callable

from betty.ancestry import Ancestry, Person, Event
from betty.functools import walk
from betty.locale import Period
from betty.parse import PostParseEvent
from betty.plugin import Plugin


class Privatizer(Plugin):
    def __init__(self):
        self._lifetime_threshold = 100

    def subscribes_to(self) -> List[Tuple[str, Callable]]:
        return (
            (PostParseEvent, lambda event: self.privatize(event.ancestry)),
        )

    def privatize(self, ancestry: Ancestry) -> None:
        for person in ancestry.people.values():
            self._privatize_person(person)

    def _privatize_person(self, person: Person) -> None:
        # Don't change existing privacy.
        if person.private is not None:
            return

        person.private = self._person_is_private(person)

    def _person_is_private(self, person: Person) -> bool:
        # A dead person is not private, regardless of when they died.
        if person.end is not None:
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
        assert multiplier > 0

        if event.date is None:
            return False

        date = event.date

        if isinstance(date, Period):
            date = date.end

        if date is None:
            return False

        if date.year is None:
            return False

        return date.year + self._lifetime_threshold * multiplier < datetime.now().year
