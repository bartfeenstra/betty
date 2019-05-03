from datetime import datetime
from typing import List, Tuple, Callable

from betty.ancestry import Ancestry, Person
from betty.functools import walk
from betty.parse import PostParseEvent
from betty.plugin import Plugin


class Anonymizer(Plugin):
    def __init__(self):
        self._consider_living_under = 125
        self._consider_living_if_unsure = True

    def subscribes_to(self) -> List[Tuple[str, Callable]]:
        return (
            (PostParseEvent, lambda event: self.anonymize(event.ancestry)),
        )

    def anonymize(self, ancestry: Ancestry) -> None:
        for person in ancestry.people.values():
            self._anonymize_person(person)

    def _consider_person_over(self, person: Person):
        return person.birth is not None and person.birth.date is not None and person.birth.date.year is not None and person.birth.date.year + self._consider_living_under < datetime.now().year

    def _consider_person_living(self, person: Person) -> bool:
        # If we have information about the person's death, they are no longer living.
        if person.death is not None:
            return False

        # If the person is considered to be over a given age, they are no longer living.
        if self._consider_person_over(person):
            return False

        # If the person's descendants are considered to be over a given age, the person is no longer living.
        descendants = walk(person, 'children')
        for descendant in descendants:
            if self._consider_person_over(descendant):
                return False

        return self._consider_living_if_unsure

    def _anonymize_person(self, person: Person) -> None:
        if not self._consider_person_living(person):
            return

        person.private = True
        person.individual_name = None
        person.family_name = None
        for event in set(person.events):
            event.people.replace(())
        for document in set(person.documents):
            document.entities.replace(())
