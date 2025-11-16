import pytest
from typing_extensions import override

from betty.content_provider import ContentProviderDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.plugin import ClassedPluginDefinitionClassTestBase


class TestContentProviderDefinition(ClassedPluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return ContentProviderDefinition
