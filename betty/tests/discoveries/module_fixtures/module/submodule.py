from betty.definition import HasDefinition
from betty.tests.discoveries.module_fixtures import PluginClsDefinition


@PluginClsDefinition("plugin-cls")
class PluginCls(HasDefinition[PluginClsDefinition]):
    pass


@PluginClsDefinition("plugin-cls-private")
class _PluginCls(HasDefinition[PluginClsDefinition]):
    pass
