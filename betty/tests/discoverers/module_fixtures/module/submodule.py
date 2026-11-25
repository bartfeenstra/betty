from betty.definition import HasDefinition
from betty.tests.discoverers.module_fixtures import ClsDefinition


@ClsDefinition()
class Cls(HasDefinition[ClsDefinition]):
    pass


@ClsDefinition()
class _Cls(HasDefinition[ClsDefinition]):
    pass
