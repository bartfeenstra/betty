"""
Media type services.
"""

from __future__ import annotations

from typing import final

from betty.media_type import MediaTypeDefinition, MediaTypeRepository
from betty.service_level import ServiceLevel
from betty.services.plugin import HasPluginServices
from betty.services.plugin.definition.collection.catalog import PluginDefinitionsService
from betty.services.simple import service


class HasMediaTypes(ServiceLevel, HasPluginServices):
    """
    Expose media types.
    """

    media_types = PluginDefinitionsService(MediaTypeDefinition)
    """
    The available media types.
    """

    # @todo Can we come up with a better name?
    @final
    @service
    def known_media_types(self) -> MediaTypeRepository:
        """
        The supported media types.
        """
        return MediaTypeRepository(*self.media_types)
