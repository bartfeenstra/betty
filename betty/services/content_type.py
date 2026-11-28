"""
Content type services.
"""

from __future__ import annotations

from typing import final

from betty.content_type import ContentTypeDefinition, ContentTypeRepository
from betty.service_level import ServiceLevel
from betty.services.plugin import HasPluginServices
from betty.services.plugin.definition.collection.catalog import PluginDefinitionsService
from betty.services.simple import service


class HasContentTypes(ServiceLevel, HasPluginServices):
    """
    Expose content types.
    """

    content_types = PluginDefinitionsService(ContentTypeDefinition)
    """
    The known content types.
    """

    # @todo Can we come up with a better name?
    @final
    @service
    def known_content_types(self) -> ContentTypeRepository:
        """
        The supported content types.
        """
        return ContentTypeRepository(*self.content_types)
