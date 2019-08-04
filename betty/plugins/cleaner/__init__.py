from collections import defaultdict
from typing import List, Tuple, Callable, Set, Type

from betty.ancestry import Ancestry, Place
from betty.graph import Graph, tsort
from betty.parse import PostParseEvent
from betty.plugin import Plugin
from betty.plugins.anonymizer import Anonymizer


def clean(ancestry: Ancestry) -> None:
    _clean_events(ancestry)
    _clean_places(ancestry)
    _clean_people(ancestry)


def _clean_events(ancestry: Ancestry):
    for event in list(ancestry.events.values()):
        if len(event.presences) == 0:
            event.place = None
            del ancestry.events[event.id]


def _clean_places(ancestry: Ancestry):
    places = list(ancestry.places.values())

    def _extend_place_graph(graph: Graph, enclosing_place: Place):
        enclosed_places = enclosing_place.encloses
        # Ensure each place appears in the graph, even if they're anonymous.
        graph.setdefault(enclosing_place, set())
        for enclosed_place in enclosed_places:
            seen_enclosed_place = enclosed_place in graph
            graph[enclosed_place].add(enclosing_place)
            if not seen_enclosed_place:
                _extend_place_graph(graph, enclosed_place)

    places_graph = defaultdict(set)
    for place in places:
        _extend_place_graph(places_graph, place)

    for place in tsort(places_graph):
        if _place_is_anonymous(place):
            place.enclosed_by = None
            del ancestry.places[place.id]


def _place_is_anonymous(place: Place) -> bool:
    if len(place.events) > 0:
        return False

    if len(place.encloses) > 0:
        return False

    return True


def _clean_people(ancestry: Ancestry) -> None:
    for person in list(ancestry.people.values()):
        if person.private and len(person.children) == 0:
            del ancestry.people[person.id]


class Cleaner(Plugin):
    @classmethod
    def comes_after(cls) -> Set[Type]:
        return {Anonymizer}

    def subscribes_to(self) -> List[Tuple[str, Callable]]:
        return (
            (PostParseEvent, lambda event: clean(event.ancestry)),
        )
