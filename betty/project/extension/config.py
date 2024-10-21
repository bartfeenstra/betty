"""
Configuration for extensions.
"""

from betty.config import Configuration
from betty.plugin.config import PluginInstanceConfiguration
from betty.project import extension
from betty.project.extension import Extension


class ExtensionInstanceConfiguration(PluginInstanceConfiguration[Extension]):
    """
    Configure a single extension instance.
    """

    def __init__(
        self,
        plugin: type[Extension],
        *,
        configuration: Configuration | None = None,
    ):
        super().__init__(
            plugin,
            configuration=configuration,
            repository=extension.EXTENSION_REPOSITORY,
        )
