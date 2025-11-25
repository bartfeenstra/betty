from collections.abc import Collection
from pathlib import Path

import pytest
from typing_extensions import override

from betty.content_provider import ContentProviderPlugin
from betty.plugin import PluginDefinition
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestContentProviderPlugin(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return ContentProviderPlugin


class TestContentProviderDocumentation(
    PluginDocumentationTestBase[ContentProviderPlugin]
):
    _plugin_type = ContentProviderPlugin
    _plugin_type_documentation_path = Path("usage") / "content-provider.rst"

    @override
    def _get_expected(self, plugin: ContentProviderPlugin) -> Collection[str]:
        return (
            *super()._get_expected(plugin),
            f"{plugin.cls.__module__}.{plugin.cls.__qualname__}",
        )
