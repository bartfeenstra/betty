from betty.definition import HasDefinition
from betty.discoveries.module import (
    ModuleClsDiscovery,
    ModuleDefinitionDiscovery,
    SubmoduleClsDiscovery,
)
from betty.tests.discoveries.module_fixtures import (
    PluginClsDefinition,
    PluginDefinitionDefinition,
)

discover_definition = ModuleDefinitionDiscovery(PluginDefinitionDefinition)
discover_cls = ModuleClsDiscovery(PluginClsDefinition)
discover_sub_cls = SubmoduleClsDiscovery(PluginClsDefinition)

plugin_definition = PluginDefinitionDefinition("plugin-definition")
_plugin_definition = PluginDefinitionDefinition("plugin-definition-private")


@PluginClsDefinition("plugin-cls")
class PluginCls(HasDefinition[PluginClsDefinition]):
    pass


@PluginClsDefinition("plugin-cls-private")
class _PluginCls(HasDefinition[PluginClsDefinition]):
    pass


@PluginClsDefinition("plugin-cls-without-has-definition")
class PluginClsWithoutHasDefinition:
    pass
