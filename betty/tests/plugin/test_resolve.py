from betty.locale.localizable import Plain
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.classed import ClassedPlugin, ClassedPluginDefinition
from betty.plugin.resolve import resolve_definition, resolve_id


def test_resolve_definition__with_plugin_cls() -> None:
    plugin_id = "my-first-plugin-id"

    class _ClassedPluginCls:
        pass

    class _ClassedPluginDefinition(ClassedPluginDefinition[_ClassedPluginCls]):
        plugin_type_cls = _ClassedPluginCls
        type = PluginTypeDefinition(
            id="-",
            label=Plain(""),
        )

    @_ClassedPluginDefinition(id=plugin_id)
    class _ClassedPlugin(_ClassedPluginCls, ClassedPlugin):
        pass

    assert resolve_definition(_ClassedPlugin) is _ClassedPlugin.plugin


def test_resolve_definition__with_plugin_definition() -> None:
    definition = PluginDefinition(id="my-first-plugin-id")
    assert resolve_definition(definition) is definition


def test_resolve_id__with_plugin_cls() -> None:
    plugin_id = "my-first-plugin-id"

    class _ClassedPluginCls:
        pass

    class _ClassedPluginDefinition(ClassedPluginDefinition[_ClassedPluginCls]):
        plugin_type_cls = _ClassedPluginCls
        type = PluginTypeDefinition(
            id="-",
            label=Plain(""),
        )

    @_ClassedPluginDefinition(id=plugin_id)
    class _ClassedPlugin(_ClassedPluginCls, ClassedPlugin):
        pass

    assert resolve_id(_ClassedPlugin) == plugin_id


def test_resolve_id__with_plugin_definition() -> None:
    plugin_id = "my-first-plugin-id"
    assert resolve_id(PluginDefinition(id=plugin_id)) == plugin_id


def test_resolve_id__with_plugin_id() -> None:
    plugin_id = "my-first-plugin-id"
    assert resolve_id(plugin_id) == plugin_id
