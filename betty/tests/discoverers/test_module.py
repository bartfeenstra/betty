from betty.discoverers.module import (
    DefinitionDiscoverer,
    HasDefinitionDiscoverer,
    SubmoduleHasDefinitionDiscoverer,
)
from betty.service_level import ServiceLevel
from betty.tests.discoverers.module_fixtures import ClsDefinition, Definition, module
from betty.tests.discoverers.module_fixtures.module import submodule


class TestDefinitionDiscoverer:
    def test___call__(self) -> None:
        sut = DefinitionDiscoverer(Definition, module.__name__)
        assert list(sut(ServiceLevel())) == [module.definition]


class TestHasDefinitionDiscoverer:
    def test___call__(self) -> None:
        sut = HasDefinitionDiscoverer(ClsDefinition, module.__name__)
        assert list(sut(ServiceLevel())) == [module.Cls.definition]


class TestSubmoduleHasDefinitionDiscoverer:
    def test___call__(self) -> None:
        sut = SubmoduleHasDefinitionDiscoverer(ClsDefinition, module.__name__)
        assert list(sut(ServiceLevel())) == [submodule.Cls.definition]
