from betty.definition import HasDefinition  # pragma: nocover
from betty.tests.discoveries.module_fixtures import (
    PluginClsDefinition,
)  # pragma: nocover


@PluginClsDefinition("plugin-cls")  # pragma: nocover
class PluginCls(HasDefinition[PluginClsDefinition]):  # pragma: nocover
    pass  # pragma: nocover
