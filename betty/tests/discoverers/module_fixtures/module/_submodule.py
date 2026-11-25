from betty.definition import HasDefinition  # pragma: nocover
from betty.tests.discoverers.module_fixtures import (
    ClsDefinition,
)  # pragma: nocover


@ClsDefinition()  # pragma: nocover
class Cls(HasDefinition[ClsDefinition]):  # pragma: nocover
    pass  # pragma: nocover
