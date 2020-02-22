from typing import List, Tuple, Callable, Set, Type

from betty.ancestry import Ancestry, Person
from betty.functools import walk
from betty.parse import PostParseEvent
from betty.plugin import Plugin
from betty.plugins.privatizer import Privatizer


def anonymize(ancestry: Ancestry) -> None:
    for person in ancestry.people.values():
        if person.private:
            anonymize_person(person)


def anonymize_person(person: Person) -> None:
    # Copy the names, because the original iterable will be altered inside the loop.
    for name in list(person.names):
        name.citations.clear()
        name.person = None

    # Copy the presences, because the original iterable will be altered inside the loop.
    for presence in list(person.presences):
        presence.person = None
        event = presence.event
        if event is not None:
            for event_presence in event.presences:
                event_presence.person = None
            event.presences.clear()

    # Copy the files, because the original iterable will be altered inside the loop.
    for file in list(person.files):
        file.resources.clear()

    # If a person is public themselves, or a node connecting other public persons, preserve their place in the graph.
    if person.private and not _has_public_descendants(person):
        person.parents.clear()


def _has_public_descendants(person: Person) -> bool:
    for descendant in walk(person, 'children'):
        if not descendant.private:
            return True
    return False


class Anonymizer(Plugin):
    @classmethod
    def comes_after(cls) -> Set[Type]:
        return {Privatizer}

    def subscribes_to(self) -> List[Tuple[Type, Callable]]:
        return [
            (PostParseEvent, lambda event: anonymize(event.ancestry)),
        ]
