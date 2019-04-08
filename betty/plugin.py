from datetime import datetime
from typing import Iterable, Callable, Tuple, Dict

from betty.ancestry import Ancestry, Person
from betty.event import POST_PARSE_EVENT
from betty.functools import walk


class Plugin:
    @classmethod
    def from_configuration_dict(cls, configuration: Dict):
        return cls()

    def subscribes_to(self) -> Iterable[Tuple[str, Callable]]:
        return []


class Anonymizer(Plugin):
    def __init__(self):
        self._consider_living_under = 125
        self._consider_living_if_unsure = True

    @classmethod
    def from_configuration_dict(cls, configuration: Dict):
        return cls()

    def subscribes_to(self) -> Iterable[Tuple[str, Callable]]:
        return (
            (POST_PARSE_EVENT, self.anonymize),
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
