from typing import override

from betty.services.plugin import (
    ResolvableServiceLevelHasPluginServices,
)
from betty.services.plugin.definition import PluginDefinitionServiceManager
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne
from betty.typing import Unreachable


class _PluginPluginDefinitionServiceManagerTestSut(
    PluginDefinitionServiceManager[
        ResolvableServiceLevelHasPluginServices,
        DummyPluginDefinition,
        DummyPluginDefinition,
    ]
):
    def __init__(self):
        super().__init__(DummyPluginDefinition)

    @override
    def new_service(
        self, owner: ResolvableServiceLevelHasPluginServices, /
    ) -> DummyPluginDefinition:
        raise Unreachable


class TestPluginDefinitionServiceManager:
    def test_resolve_init_plugin_id__with_plugin_manufacturer(self) -> None:
        assert (
            _PluginPluginDefinitionServiceManagerTestSut().resolve_init_plugin_id(
                DummyPluginOne
            )
            == DummyPluginOne.definition.id
        )
