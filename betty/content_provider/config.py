"""
Content provider configuration.
"""

from collections.abc import Sequence
from typing import TypeAlias

from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.plugin.config import (
    PluginInstanceConfiguration,
    PluginInstanceConfigurationSequence,
)

ShorthandContentProviderInstanceConfigurationSequence: TypeAlias = (
    Sequence[PluginInstanceConfiguration[ContentProviderDefinition, ContentProvider]]
    | None
)

ContentProviderInstanceConfigurationSequence: TypeAlias = (
    PluginInstanceConfigurationSequence[ContentProviderDefinition, ContentProvider]
)
