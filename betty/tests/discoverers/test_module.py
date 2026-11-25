from betty.discoverers.module import (
    ModuleClsDiscovery,
    ModuleDefinitionDiscovery,
    SubmoduleClsDiscovery,
)
from betty.service_level import ServiceLevel
from betty.tests.discoverers.module_fixtures import ClsDefinition, Definition, module
from betty.tests.discoverers.module_fixtures.module import submodule


class TestModuleDefinitionDiscovery:
    def test___call____with_auto_module(self) -> None:
        assert list(module.discover_definition(ServiceLevel())) == [module.definition]

    def test___call____with_module(self) -> None:
        sut = ModuleDefinitionDiscovery(Definition, module.__name__)
        assert list(sut(ServiceLevel())) == [module.definition]


class TestModuleClsDiscovery:
    def test___call____with_auto_module(self) -> None:
        assert list(module.discover_cls(ServiceLevel())) == [module.Cls.definition]

    def test___call____with_module(self) -> None:
        sut = ModuleClsDiscovery(ClsDefinition, module.__name__)
        assert list(sut(ServiceLevel())) == [module.Cls.definition]


class TestSubmoduleClsDiscovery:
    def test___call____with_auto_module(self) -> None:
        assert list(module.discover_sub_cls(ServiceLevel())) == [
            submodule.Cls.definition
        ]

    def test___call____with_module(self) -> None:
        sut = SubmoduleClsDiscovery(ClsDefinition, module.__name__)
        assert list(sut(ServiceLevel())) == [submodule.Cls.definition]
