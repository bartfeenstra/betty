from typing import Set, Type, Any

from betty.ancestry import Ancestry, Person, File, Citation, Source, Event
from betty.functools import walk
from betty.parse import PostParser
from betty.plugin import Plugin, NO_CONFIGURATION
from betty.plugin.privatizer import Privatizer
from betty.site import Site


class AnonymousSource(Source):
    def __init__(self):
        Source.__init__(self, _('Private'))

    def replace(self, other: Source) -> None:
        self.citations.append(*other.citations)
        self.contains.append(*other.contains)
        self.files.append(*other.files)


class AnonymousCitation(Citation):
    def __init__(self, source: Source):
        Citation.__init__(self, source)
        self.location = _("A citation is available, but has not been published in order to protect people's privacy")

    def replace(self, other: Citation) -> None:
        self.facts.append(*other.facts)
        self.files.append(*other.files)


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
    for name in person.names:
        del name.citations
    del person.names
    del person.citations
    del person.files
    for presence in person.presences:
        del presence.event
    del person.presences

    # If a person connects other public people, keep them in the person graph.
    if person.private and not _has_public_descendants(person):
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


def anonymize_source(source: Source, anonymous_source: AnonymousSource) -> None:
    anonymous_source.replace(source)
    del source.citations
    del source.contained_by
    del source.contains
    del source.files


def anonymize_citation(citation: Citation, anonymous_citation: AnonymousCitation) -> None:
    anonymous_citation.replace(citation)
    del citation.facts
    del citation.files
    del citation.source


class Anonymizer(Plugin, PostParser):
    def __init__(self, ancestry: Ancestry):
        self._ancestry = ancestry

    @classmethod
    def for_site(cls, site: Site, configuration: Any = NO_CONFIGURATION):
        return cls(site.ancestry)

    @classmethod
    def comes_after(cls) -> Set[Type[Plugin]]:
        return {Privatizer}

    async def post_parse(self) -> None:
        anonymize(self._ancestry)
