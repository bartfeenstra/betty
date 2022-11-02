from typing import Set, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from betty.builtins import _

from betty.app.extension import Extension, UserFacingExtension
from betty.privatizer import Privatizer
from betty.model.ancestry import Ancestry, Person, File, Citation, Source, Event
from betty.functools import walk
from betty.load import PostLoader


class AnonymousSource(Source):
    _ID = 'betty-anonymous-source'

    def __init__(self):
        super().__init__(self._ID)

    @property  # type: ignore
    def name(self) -> str:  # type: ignore
        return _('Private')

    @name.setter
    def name(self, _) -> None:
        # This is a no-op as the name is 'hardcoded'.
        pass

    @name.deleter
    def name(self) -> None:
        # This is a no-op as the name is 'hardcoded'.
        pass

    def replace(self, other: Source, ancestry: Ancestry) -> None:
        if isinstance(other, AnonymousSource):
            return

        self.citations.append(*other.citations)
        other.citations.clear()
        self.contains.append(*other.contains)
        other.contains.clear()
        self.files.append(*other.files)
        other.files.clear()
        ancestry.entities[Source].remove(other)


class AnonymousCitation(Citation):
    _ID = 'betty-anonymous-citation'

    def __init__(self, source: Source):
        super().__init__(self._ID, source)

    @property  # type: ignore
    def location(self) -> str:  # type: ignore
        return _("A citation is available, but has not been published in order to protect people's privacy")

    @location.setter
    def location(self, _) -> None:
        # This is a no-op as the location is 'hardcoded'.
        pass

    @location.deleter
    def location(self) -> None:
        # This is a no-op as the location is 'hardcoded'.
        pass

    def replace(self, other: Citation, ancestry: Ancestry) -> None:
        if isinstance(other, AnonymousCitation):
            return

        self.facts.append(*other.facts)
        other.facts.clear()
        self.files.append(*other.files)
        other.files.clear()
        ancestry.entities[Citation].remove(other)


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
            anonymize_source(source, ancestry, anonymous_source)
    for citation in ancestry.entities[Citation]:
        if citation.private:
            anonymize_citation(citation, ancestry, anonymous_citation)


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


def anonymize_source(source: Source, ancestry: Ancestry, anonymous_source: AnonymousSource) -> None:
    if isinstance(source, AnonymousSource):
        return

    anonymous_source.replace(source, ancestry)
    for citation in source.citations:
        if not isinstance(citation, AnonymousCitation):
            source.citations.remove(citation)
    del source.contained_by
    del source.contains
    del source.files


def anonymize_citation(citation: Citation, ancestry: Ancestry, anonymous_citation: AnonymousCitation) -> None:
    if isinstance(citation, AnonymousCitation):
        return

    anonymous_citation.replace(citation, ancestry)
    del citation.facts
    del citation.files
    if not isinstance(citation.source, AnonymousSource):
        del citation.source


class Anonymizer(UserFacingExtension, PostLoader):
    @classmethod
    def comes_after(cls) -> Set[Type[Extension]]:
        return {Privatizer}

    async def post_load(self) -> None:
        anonymize(self.app.project.ancestry, AnonymousCitation(AnonymousSource()))

    @classmethod
    def label(cls) -> str:
        return _('Anonymizer')

    @classmethod
    def description(cls) -> str:
        return _('Anonymize people, events, files, sources, and citations marked private by removing their information and relationships with other resources. Enable the Privatizer and Cleaner as well to make this most effective.')
