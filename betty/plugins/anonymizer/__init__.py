from typing import List, Tuple, Callable, Set, Type, Optional

from betty.ancestry import Ancestry, Person, File, Citation, Source, Event
from betty.event import Event as DispatchedEvent
from betty.functools import walk
from betty.parse import PostParseEvent
from betty.plugin import Plugin
from betty.plugins.privatizer import Privatizer


class AnonymousSource(Source):
    def __init__(self):
        Source.__init__(self, _('Private'))


class AnonymousCitation(Citation):
    def __init__(self, source: Source):
        Citation.__init__(self, source)

    @property
    def location(self) -> Optional[str]:
        return _("This citation has not been published in order to protect people's privacy.")

    def assimilate(self, other: Citation) -> None:
        self.facts.append(*other.facts)


def anonymize(ancestry: Ancestry) -> None:
    anonymous_source = AnonymousSource()
    anonymous_citation = AnonymousCitation(anonymous_source)
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
            anonymize_source(source, anonymous_source)
    for citation in ancestry.citations.values():
        if citation.private:
            anonymize_citation(citation, anonymous_citation)


def anonymize_person(person: Person) -> None:
    del person.citations
    del person.files
    del person.names
    del person.presences

    # If a person connects other public people, keep them in the person graph.
    if not _has_public_descendants(person):
        del person.parents

    # If a person is public themselves, or a node connecting other public persons, preserve their place in the graph.
    if person.private and not _has_public_descendants(person):
        person.parents.clear()


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


def anonymize_source(source: Source, anonymous_source: AnonymousSource) -> None:
    # @todo assimilate
    del source.citations
    del source.contained_by
    del source.contains
    del source.files


def anonymize_citation(citation: Citation, anonymous_citation: AnonymousCitation) -> None:
    # @todo assimilate
    del citation.facts
    del citation.files
    del citation.source


class Anonymizer(Plugin):
    @classmethod
    def comes_after(cls) -> Set[Type[Plugin]]:
        return {Privatizer}

    def subscribes_to(self) -> List[Tuple[Type[DispatchedEvent], Callable]]:
        return [
            (PostParseEvent, lambda event: anonymize(event.ancestry)),
        ]
