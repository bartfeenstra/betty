from typing import Set, Type

from betty.model.ancestry import Ancestry, Person, File, Citation, Source, Event
from betty.functools import walk
from betty.gui import GuiBuilder
from betty.load import PostLoader
from betty.extension import Extension
from betty.extension.privatizer import Privatizer


class AnonymousSource(Source):
    _ID = 'betty-anonymous-source'

    def __init__(self):
        super().__init__(self._ID, _('Private'))

    def replace(self, other: Source) -> None:
        self.citations.append(*other.citations)
        self.contains.append(*other.contains)
        self.files.append(*other.files)


class AnonymousCitation(Citation):
    _ID = 'betty-anonymous-citation'

    def __init__(self, source: Source):
        super().__init__(self._ID, source)
        self.location = _("A citation is available, but has not been published in order to protect people's privacy")

    def replace(self, other: Citation) -> None:
        self.facts.append(*other.facts)
        self.files.append(*other.files)


def anonymize(ancestry: Ancestry, anonymous_citation: AnonymousCitation) -> None:
    anonymous_source = anonymous_citation.source
    if not isinstance(anonymous_source, AnonymousSource):
        raise ValueError(f"The anonymous citation's source must be a {AnonymousSource}")

    for person in ancestry.entities[Person]:
        if person.private:
            anonymize_person(person)
    for event in ancestry.entities[Event]:
        if event.private:
            anonymize_event(event)
    for file in ancestry.entities[File]:
        if file.private:
            anonymize_file(file)
    for source in ancestry.entities[Source]:
        if source.private:
            anonymize_source(source, anonymous_source)
    for citation in ancestry.entities[Citation]:
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
    del file.entities


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


class Anonymizer(Extension, PostLoader, GuiBuilder):
    @classmethod
    def comes_after(cls) -> Set[Type[Extension]]:
        return {Privatizer}

    async def post_load(self) -> None:
        anonymize(self._app.ancestry, AnonymousCitation(AnonymousSource()))

    @classmethod
    def gui_name(cls) -> str:
        return _('Anonymizer')

    @classmethod
    def gui_description(cls) -> str:
        return _('Anonymize people, events, files, sources, and citations marked private by removing their information and relationships with other resources. Enable the Privatizer and Cleaner as well to make this most effective.')
