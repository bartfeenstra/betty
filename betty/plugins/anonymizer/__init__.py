from typing import List, Tuple, Callable, Set, Type

from betty.ancestry import Ancestry, Person
from betty.parse import PostParseEvent
from betty.plugin import Plugin
from betty.plugins.privatizer import Privatizer


class Anonymizer(Plugin):
    @classmethod
    def comes_after(cls) -> Set[Type]:
        return {Privatizer}

    def subscribes_to(self) -> List[Tuple[str, Callable]]:
        return (
            (PostParseEvent, lambda event: self.anonymize(event.ancestry)),
        )

    def anonymize(self, ancestry: Ancestry) -> None:
        for person in ancestry.people.values():
            self._anonymize_person(person)

    def _anonymize_person(self, person: Person) -> None:
        if not person.private:
            return

        person.individual_name = None
        person.family_name = None
        for event in set(person.events):
            event.people.remove(person)
        for document in set(person.documents):
            document.entities.remove(person)
