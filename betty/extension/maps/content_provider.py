"""
Map content.
"""

from collections.abc import Iterable, Mapping
from typing import Any, Self

from typing_extensions import override

from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.document import Document
from betty.extension.maps import Maps
from betty.locale.localizable.gettext import _
from betty.service.level import Manufacturable
from betty.service.requirement.extension import require_extension


@ContentProviderDefinition("maps-map", label=_("Map"))
class Map(Template, Manufacturable):
    """
    An interactive map.

    .. plugin:: content-provider:maps-map
    """

    @override
    @classmethod
    @require_extension(Maps)
    async def new(cls, *, extension: Maps) -> Self:
        return cls(jinja=await extension.services.jinja)

    @override
    async def provide_template(
        self, document: Document
    ) -> str | Iterable[str] | tuple[str | Iterable[str], Mapping[str, Any]] | None:
        places = []
        if isinstance(document.resource, Event) and document.resource.place:
            places.append(document.resource.place)
        elif isinstance(document.resource, Person):
            places.extend(
                presence.event.place
                for presence in document.resource.presences
                if presence.public
                and presence.event.public
                and presence.event.place
                and presence.event.place.public
            )
        elif isinstance(document.resource, Place):
            places.append(
                document.resource,
            )
        if places:
            return "component/maps/map.html.j2", {
                "places": places,
            }
        return None


@ContentProviderDefinition("maps-attribution", label=_("Map attribution"))
class Attribution(Template, Manufacturable):
    """
    The attribution for an interactive map.

    .. plugin:: content-provider:maps-attribution
    """

    @override
    @classmethod
    @require_extension(Maps)
    async def new(cls, *, extension: Maps) -> Self:
        return cls(jinja=await extension.services.jinja)

    @override
    async def provide_template(
        self, document: Document
    ) -> str | Iterable[str] | tuple[str | Iterable[str], Mapping[str, Any]] | None:
        return "component/maps/attribution.html.j2"
