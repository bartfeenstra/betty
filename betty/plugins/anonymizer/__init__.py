from typing import List, Tuple, Callable, Set, Type

from betty.ancestry import Ancestry, Person, Event, File, Citation, Source
from betty.functools import walk
from betty.parse import PostParseEvent
from betty.plugin import Plugin
from betty.plugins.privatizer import Privatizer


def anonymize(ancestry: Ancestry) -> None:
    for person in ancestry.people.values():
        if person.private:
            anonymize_person(person)
    for event in ancestry.events.values():
        if event.private:
            anonymize_event(event)
    for file in ancestry.files.values():
        if file.private:
            anonymize_file(file)
    for source in ancestry.sources.values():
        if source.private:
            anonymize_source(source)
    for citation in ancestry.citations.values():
        if citation.private:
            anonymize_citation(citation)


def anonymize_person(person: Person) -> None:
    del person.citations
    del person.files
    del person.names
    del person.presences

    # If a person connects other public people, keep them in the person graph.
    if not _has_public_descendants(person):
        del person.parents


def _has_public_descendants(person: Person) -> bool:
    for descendant in walk(person, 'children'):
        if not descendant.private:
            return True
    return False


def anonymize_event(event: Event) -> None:
    del event.citations
    del event.files
    del event.presences


def anonymize_file(file: File) -> None:
    del file.resources


def anonymize_source(source: Source) -> None:
    del source.citations
    del source.contained_by
    del source.contains
    del source.files


def anonymize_citation(citation: Citation) -> None:
    del citation.facts
    del citation.files
    del citation.source


class Anonymizer(Plugin):
    @classmethod
    def comes_after(cls) -> Set[Type]:
        return {Privatizer}

    def subscribes_to(self) -> List[Tuple[Type, Callable]]:
        return [
            (PostParseEvent, lambda event: anonymize(event.ancestry)),
        ]
