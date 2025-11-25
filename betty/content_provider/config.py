"""
Content provider configuration.
"""

from collections.abc import Sequence
from typing import TypeAlias

from betty.content_provider import ContentProvider, ContentProviderPlugin
from betty.plugin.config import (
    PluginInstanceConfiguration,
    PluginInstanceConfigurationSequence,
)

ShorthandContentProviderInstanceConfigurationSequence: TypeAlias = (
    Sequence[PluginInstanceConfiguration[ContentProviderPlugin, ContentProvider]] | None
)

ContentProviderInstanceConfigurationSequence: TypeAlias = (
    PluginInstanceConfigurationSequence[ContentProviderPlugin, ContentProvider]
)
