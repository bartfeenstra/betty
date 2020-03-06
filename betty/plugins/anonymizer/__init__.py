from typing import List, Tuple, Callable, Set, Type, Optional

from betty.ancestry import Ancestry, Person, Citation, File, Source
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


class AncestryAnonymizer:
    def __init__(self, ancestry: Ancestry):
        self._ancestry = ancestry
        self._source = AnonymousSource()
        self._citation = AnonymousCitation(self._source)

    def anonymize(self) -> None:
        for person in self._ancestry.people.values():
            if person.private:
                self.anonymize_person(person)
        for file in self._ancestry.files.values():
            if file.private:
                self._anonymize_file(file)
        for source in self._ancestry.sources.values():
            if source.private:
                self._anonymize_source(source)
        for citation in self._ancestry.citations.values():
            if citation.private:
                self._anonymize_citation(citation)

    def anonymize_person(self, person: Person) -> None:
        # Copy the names, because the original iterable will be altered inside the loop.
        for name in person.names:
            for citation in person.citations:
                self._anonymize_citation(citation)
            name.citations.clear()

        # Copy the presences, because the original iterable will be altered inside the loop.
        for presence in list(person.presences):
            presence.person = None
            event = presence.event
            if event is not None:
                for event_presence in event.presences:
                    event_presence.person = None
                event.presences.clear()

        # If a person is public themselves, or a node connecting other public persons, preserve their place in the graph.
        if person.private and not self._has_public_descendants(person):
            person.parents.clear()

    def _has_public_descendants(self, person: Person) -> bool:
        for descendant in walk(person, 'children'):
            if not descendant.private:
                return True
        return False

    def _anonymize_source(self, source: Source) -> None:
        # @todo assimilate
        pass

    def _anonymize_citation(self, citation: Citation) -> None:
        # @todo assimilate
        citation.source = None
        citation.facts.clear()

    def _anonymize_file(self, file: File) -> None:
        file.resources.clear()


class Anonymizer(Plugin):
    @classmethod
    def comes_after(cls) -> Set[Type]:
        return {Privatizer}

    def subscribes_to(self) -> List[Tuple[Type, Callable]]:
        return [
            (PostParseEvent, lambda event: AncestryAnonymizer(event.ancestry).anonymize()),
        ]
