from collections import defaultdict

from betty.anonymizer import Anonymizer
from betty.app.extension import Extension

try:
    from graphlib import TopologicalSorter
except ImportError:
    from graphlib_backport import TopologicalSorter  # type: ignore
from typing import Set, Type, Dict, TYPE_CHECKING

from betty.model.ancestry import Ancestry, Place, File, Person, Event, Source, Citation
from betty.gui import GuiBuilder
from betty.load import PostLoader

if TYPE_CHECKING:
    from betty.builtins import _


def clean(ancestry: Ancestry) -> None:
    _clean_people(ancestry)
    _clean_events(ancestry)
    _clean_places(ancestry)
    _clean_files(ancestry)
    _clean_citations(ancestry)
    _clean_sources(ancestry)


def _clean_events(ancestry: Ancestry) -> None:
    for event in ancestry.entities[Event]:
        _clean_event(ancestry, event)


def _clean_event(ancestry: Ancestry, event: Event) -> None:
    if len(event.presences) > 0:
        return

    del event.presences
    del event.place
    del event.citations
    del event.files
    del ancestry.entities[Event][event]


def _clean_places(ancestry: Ancestry) -> None:
    places = ancestry.entities[Place]

    def _extend_place_graph(graph: Dict, enclosing_place: Place) -> None:
        enclosures = enclosing_place.encloses
        # Ensure each place appears in the graph, even if they're anonymous.
        graph.setdefault(enclosing_place, set())
        for enclosure in enclosures:
            enclosed_place = enclosure.encloses
            seen_enclosed_place = enclosed_place in graph
            graph[enclosing_place].add(enclosed_place)
            if not seen_enclosed_place:
                _extend_place_graph(graph, enclosed_place)

    places_graph = defaultdict(set)
    for place in places:
        _extend_place_graph(places_graph, place)

    for place in TopologicalSorter(places_graph).static_order():
        _clean_place(ancestry, place)


def _clean_place(ancestry: Ancestry, place: Place) -> None:
    if len(place.events) > 0:
        return

    if len(place.encloses) > 0:
        return

    del place.enclosed_by
    del ancestry.entities[Place][place]


def _clean_people(ancestry: Ancestry) -> None:
    for person in ancestry.entities[Person]:
        _clean_person(ancestry, person)


def _clean_person(ancestry: Ancestry, person: Person) -> None:
    if not person.private:
        return

    if len(person.children) > 0:
        return

    del ancestry.entities[Person][person]


def _clean_files(ancestry: Ancestry) -> None:
    for file in ancestry.entities[File]:
        _clean_file(ancestry, file)


def _clean_file(ancestry: Ancestry, file: File) -> None:
    if len(file.entities) > 0:
        return

    if len(file.citations) > 0:
        return

    del ancestry.entities[File][file]


def _clean_sources(ancestry: Ancestry) -> None:
    for source in ancestry.entities[Source]:
        _clean_source(ancestry, source)


def _clean_source(ancestry: Ancestry, source: Source) -> None:
    if len(source.citations) > 0:
        return

    if source.contained_by is not None:
        return

    if len(source.contains) > 0:
        return

    if len(source.files) > 0:
        return

    del ancestry.entities[Source][source]


def _clean_citations(ancestry: Ancestry) -> None:
    for citation in ancestry.entities[Citation]:
        _clean_citation(ancestry, citation)


def _clean_citation(ancestry: Ancestry, citation: Citation) -> None:
    if len(citation.facts) > 0:
        return

    if len(citation.files) > 0:
        return

    del citation.source
    del ancestry.entities[Citation][citation]


class Cleaner(Extension, PostLoader, GuiBuilder):
    @classmethod
    def comes_after(cls) -> Set[Type[Extension]]:
        return {Anonymizer}

    async def post_load(self) -> None:
        clean(self._app.ancestry)

    @classmethod
    def label(cls) -> str:
        return _('Cleaner')

    @classmethod
    def gui_description(cls) -> str:
        return _('Remove people, events, places, files, sources, and citations if they have no relationships with any other resources. Enable the Privatizer and Anonymizer as well to make this most effective.')
