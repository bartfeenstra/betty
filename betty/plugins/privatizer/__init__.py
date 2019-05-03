from datetime import datetime
from typing import List, Tuple, Callable

from betty.ancestry import Ancestry, Person
from betty.functools import walk
from betty.parse import PostParseEvent
from betty.plugin import Plugin


class Privatizer(Plugin):
    def __init__(self):
        self._privacy_expires_at_age = 125

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

        person.private = self._person_has_privacy(person)

    def _person_has_privacy(self, person: Person) -> bool:
        return not self._person_is_dead(person) and not self._person_has_expired(
            person) and not self._descendants_have_expired(person)

    def _person_is_dead(self, person: Person) -> bool:
        return person.death is not None

    def _person_has_expired(self, person: Person) -> bool:
        return person.birth is not None and person.birth.date is not None and person.birth.date.year is not None and person.birth.date.year + self._privacy_expires_at_age < datetime.now().year

    def _descendants_have_expired(self, person: Person) -> bool:
        descendants = walk(person, 'children')
        for descendant in descendants:
            if self._person_has_expired(descendant):
                return True
