import pytest
from typing_extensions import override

from betty.ancestry.presence_role import PresenceRolePlugin
from betty.plugin import PluginDefinition
from betty.test_utils.plugin import PluginDefinitionClassTestBase


class TestPresenceRolePlugin(PluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return PresenceRolePlugin
