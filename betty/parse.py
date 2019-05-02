from betty.event import PARSE_EVENT, POST_PARSE_EVENT
from betty.site import Site


def parse(site: Site) -> None:
    site.event_dispatcher.dispatch(PARSE_EVENT, site.ancestry)
    site.event_dispatcher.dispatch(POST_PARSE_EVENT, site.ancestry)
