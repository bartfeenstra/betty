import pytest
from typing_extensions import override

from betty.ancestry.presence_role import PresenceRoleDefinition
from betty.plugin import PluginDefinition
from betty.test_utils.plugin import ClassedPluginDefinitionClassTestBase


class TestPresenceRoleDefinition(ClassedPluginDefinitionClassTestBase):
    @override
    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        return PresenceRoleDefinition
