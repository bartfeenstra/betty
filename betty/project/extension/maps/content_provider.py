"""
Map content.
"""

from collections.abc import Mapping
from typing import Any

from typing_extensions import override

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.locale.localizable.gettext import _
from betty.project.extension.maps import Maps
from betty.requirement import HasRequirement, Requirement
from betty.resource import Context as ResourceContext
from betty.service.level import ServiceLevel


@ContentProviderDefinition("maps-map", label=_("Map"))
class Map(Template, HasRequirement):
    """
    An interactive map.
    """

    @override
    async def _provide_data(self, resource: ResourceContext) -> Mapping[str, Any]:
        return {
            "entity": resource.resource,
        }

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        return await Maps.requirement_for(
            services, cls.plugin().reference_label_with_type
        )
