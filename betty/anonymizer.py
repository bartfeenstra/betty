from __future__ import annotations

from betty.functools import walk
from betty.locale import Localizer
from betty.model.ancestry import Ancestry, Person, File, Citation, Source, Event


class AnonymousSource(Source):
    _ID = 'betty-anonymous-source'

    def __init__(self, *, localizer: Localizer | None = None):
        super().__init__(self._ID, localizer=localizer)

    @property  # type: ignore[override]
    def name(self) -> str:
        return self.localizer._('Private')

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

        self.citations.add(*other.citations)
        other.citations.clear()
        self.contains.add(*other.contains)
        other.contains.clear()
        self.files.add(*other.files)
        other.files.clear()
        ancestry[Source].remove(other)


class AnonymousCitation(Citation):
    _ID = 'betty-anonymous-citation'

    def __init__(self, source: Source, *, localizer: Localizer | None = None):
        super().__init__(self._ID, source, localizer=localizer)

    @property  # type: ignore[override]
    def location(self) -> str:
        return self.localizer._("A citation is available, but has not been published in order to protect people's privacy")

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

        self.facts.add(*other.facts)
        other.facts.clear()
        self.files.add(*other.files)
        other.files.clear()
        ancestry[Citation].remove(other)


def anonymize(ancestry: Ancestry, anonymous_citation: AnonymousCitation) -> None:
    anonymous_source = anonymous_citation.source
    if not isinstance(anonymous_source, AnonymousSource):
        raise ValueError(f"The anonymous citation's source must be a {AnonymousSource}")

    for person in ancestry[Person]:
        if person.private:
            anonymize_person(person)
    for event in ancestry[Event]:
        if event.private:
            anonymize_event(event)
    for file in ancestry[File]:
        if file.private:
            anonymize_file(file)
    for source in ancestry[Source]:
        if source.private:
            anonymize_source(source, ancestry, anonymous_source)
    for citation in ancestry[Citation]:
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
