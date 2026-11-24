from betty.discoveries.module import (
    ModuleClsDiscovery,
    ModuleDefinitionDiscovery,
    SubmoduleClsDiscovery,
)
from betty.service_level import ServiceLevel
from betty.tests.discoveries.module_fixtures import (
    PluginClsDefinition,
    PluginDefinitionDefinition,
    module,
)
from betty.tests.discoveries.module_fixtures.module import submodule


class TestModuleDefinitionDiscovery:
    def test___call____with_auto_module(self) -> None:
        assert list(module.discover_definition(ServiceLevel())) == [
            module.plugin_definition
        ]

    def test___call____with_module(self) -> None:
        sut = ModuleDefinitionDiscovery(PluginDefinitionDefinition, module.__name__)
        assert list(sut(ServiceLevel())) == [module.plugin_definition]


class TestModuleClsDiscovery:
    def test___call____with_auto_module(self) -> None:
        assert list(module.discover_cls(ServiceLevel())) == [
            module.PluginCls.definition
        ]

    def test___call____with_module(self) -> None:
        sut = ModuleClsDiscovery(PluginClsDefinition, module.__name__)
        assert list(sut(ServiceLevel())) == [module.PluginCls.definition]


class TestSubmoduleClsDiscovery:
    def test___call____with_auto_module(self) -> None:
        assert list(module.discover_sub_cls(ServiceLevel())) == [
            submodule.PluginCls.definition
        ]

    def test___call____with_module(self) -> None:
        sut = SubmoduleClsDiscovery(PluginClsDefinition, module.__name__)
        assert list(sut(ServiceLevel())) == [submodule.PluginCls.definition]
