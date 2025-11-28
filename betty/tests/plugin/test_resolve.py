from betty.locale.localizable import CountablePlain
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.resolve import resolve_definition, resolve_id


def test_resolve_definition__with_plugin_cls() -> None:
    plugin_id = "my-first-plugin-id"

    class _PluginCls(Plugin):
        pass

    class _PluginDefinition(PluginDefinition):
        plugin_type_cls = _PluginCls
        type = PluginTypeDefinition("-", "", "", CountablePlain("", ""))

    @_PluginDefinition(plugin_id)
    class _Plugin(_PluginCls, Plugin):
        pass

    assert resolve_definition(_Plugin) is _Plugin.plugin


def test_resolve_definition__with_plugin_definition() -> None:
    definition = PluginDefinition("my-first-plugin-id")
    assert resolve_definition(definition) is definition


def test_resolve_id__with_plugin_cls() -> None:
    plugin_id = "my-first-plugin-id"

    class _PluginCls(Plugin):
        pass

    class _PluginDefinition(PluginDefinition):
        plugin_type_cls = _PluginCls
        type = PluginTypeDefinition("-", "", "", CountablePlain("", ""))

    @_PluginDefinition(plugin_id)
    class _Plugin(_PluginCls, Plugin):
        pass

    assert resolve_id(_Plugin) == plugin_id


def test_resolve_id__with_plugin_definition() -> None:
    plugin_id = "my-first-plugin-id"
    assert resolve_id(PluginDefinition(plugin_id)) == plugin_id


def test_resolve_id__with_plugin_id() -> None:
    plugin_id = "my-first-plugin-id"
    assert resolve_id(plugin_id) == plugin_id
