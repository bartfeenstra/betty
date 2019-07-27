from betty.ancestry import Ancestry
from betty.event import Event
from betty.site import Site


class ParseEvent(Event):
    def __init__(self, ancestry: Ancestry):
        self._ancestry = ancestry

    @property
    def ancestry(self):
        return self._ancestry


class PostParseEvent(Event):
    def __init__(self, ancestry: Ancestry):
        self._ancestry = ancestry

    @property
    def ancestry(self):
        return self._ancestry


def parse(site: Site) -> None:
    site.event_dispatcher.dispatch(ParseEvent(site.ancestry))
    site.event_dispatcher.dispatch(PostParseEvent(site.ancestry))
