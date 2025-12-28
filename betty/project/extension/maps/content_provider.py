"""
Map content.
"""

from collections.abc import Mapping
from typing import Any

from typing_extensions import override

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.document import Document
from betty.locale.localizable.gettext import _
from betty.project.extension.maps import Maps
from betty.requirement import HasRequirement, Requirement
from betty.service.level import ServiceLevel


@ContentProviderDefinition("maps-map", label=_("Map"))
class Map(Template, HasRequirement):
    """
    An interactive map.
    """

    @override
    async def _provide_data(self, document: Document) -> Mapping[str, Any]:
        return {
            "entity": document.resource,
        }

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        return await Maps.requirement_for(
            services, cls.plugin().reference_label_with_type
        )
