"""
Map content.
"""

from collections.abc import Mapping
from typing import Any

from typing_extensions import override

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.locale.localizable import _
from betty.resource import Context as ResourceContext


@ContentProviderDefinition(
    id="maps-map",
    label=_("Map"),
)
class Map(Template):
    """
    An interactive map.
    """

    @override
    async def _provide_data(self, resource: ResourceContext) -> Mapping[str, Any]:
        return {
            "entity": resource["resource"],
        }
