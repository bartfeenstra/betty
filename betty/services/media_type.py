"""
Media type services.
"""

from __future__ import annotations

from typing import final

from betty.content_type import ContentTypeDefinition, ContentTypeRepository
from betty.service_level import ServiceLevel
from betty.services.plugin import HasPluginServices
from betty.services.plugin.definition.collection.catalog import PluginDefinitionsService
from betty.services.simple import service


class HasMediaTypes(ServiceLevel, HasPluginServices):
    """
    Expose media types.
    """

    media_types = PluginDefinitionsService(ContentTypeDefinition)
    """
    The available media types.
    """

    # @todo Can we come up with a better name?
    @final
    @service
    def known_media_types(self) -> ContentTypeRepository:
        """
        The supported media types.
        """
        return ContentTypeRepository(*self.media_types)
