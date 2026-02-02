"""
Map content.
"""

from collections.abc import Mapping
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
    async def new_for_services(cls, *, extension: Maps) -> Self:
        return cls(jinja2_environment=await extension._project.jinja2_environment)

    @override
    async def _provide_data(self, document: Document) -> Mapping[str, Any]:
        places = []
        if isinstance(document.resource, Event):
            places = [document.resource.place] if document.resource.place else []
        elif isinstance(document.resource, Person):
            places = [
                presence.event.place
                for presence in document.resource.presences
                if presence.public
                and presence.event.public
                and presence.event.place
                and presence.event.place.public
            ]
        elif isinstance(document.resource, Place):
            places = [
                document.resource,
            ]
        return {
            "places": places,
        }


@ContentProviderDefinition("maps-map-attribution", label=_("Map attribution"))
class MapAttribution(Template, Manufacturable):
    """
    The attribution for an interactive map.

    .. plugin:: content-provider:maps-map-attribution
    """

    @override
    @classmethod
    @require_extension(Maps)
    async def new_for_services(cls, *, extension: Maps) -> Self:
        return cls(jinja2_environment=await extension._project.jinja2_environment)
