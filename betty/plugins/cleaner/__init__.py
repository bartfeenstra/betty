from typing import List, Tuple, Callable, Set, Type

from betty.ancestry import Ancestry
from betty.parse import PostParseEvent
from betty.plugin import Plugin
from betty.plugins.anonymizer import Anonymizer


def clean(ancestry: Ancestry) -> None:
    for event in list(ancestry.events.values()):
        if len(event.people) == 0:
            event.place = None
            del ancestry.events[event.id]

    for place in list(ancestry.places.values()):
        if len(place.events) == 0:
            del ancestry.places[place.id]


class Cleaner(Plugin):
    @classmethod
    def comes_after(cls) -> Set[Type]:
        return {Anonymizer}

    def subscribes_to(self) -> List[Tuple[str, Callable]]:
        return (
            (PostParseEvent, lambda event: clean(event.ancestry)),
        )
