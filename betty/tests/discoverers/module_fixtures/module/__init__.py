from betty.definition import HasDefinition
from betty.discoverers.module import (
    ModuleClsDiscovery,
    ModuleDefinitionDiscovery,
    SubmoduleClsDiscovery,
)
from betty.tests.discoverers.module_fixtures import (
    ClsDefinition,
    Definition,
)

discover_definition = ModuleDefinitionDiscovery(Definition)
discover_cls = ModuleClsDiscovery(ClsDefinition)
discover_sub_cls = SubmoduleClsDiscovery(ClsDefinition)

definition = Definition()
_definition = Definition()


@ClsDefinition()
class Cls(HasDefinition[ClsDefinition]):
    pass


@ClsDefinition()
class _Cls(HasDefinition[ClsDefinition]):
    pass


@ClsDefinition()
class ClsWithoutHasDefinition:
    pass
