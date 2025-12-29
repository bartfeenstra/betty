from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.resolve import resolve_definition, resolve_id
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)


class _PluginCls(Plugin["_PluginDefinition"]):
    pass


@PluginTypeDefinition(
    "-",
    base_cls=_PluginCls,
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _PluginDefinition(PluginDefinition[_PluginCls]):
    pass


def test_resolve_definition__with_plugin_cls() -> None:
    plugin_id = "my-first-plugin-id"

    @_PluginDefinition(plugin_id)
    class _Plugin(_PluginCls):
        pass

    assert resolve_definition(_Plugin) is _Plugin.plugin()


def test_resolve_definition__with_plugin_definition() -> None:
    definition = PluginDefinition("my-first-plugin-id")
    assert resolve_definition(definition) is definition


def test_resolve_id__with_plugin_cls() -> None:
    plugin_id = "my-first-plugin-id"

    @_PluginDefinition(plugin_id)
    class _Plugin(_PluginCls):
        pass

    assert resolve_id(_Plugin) == plugin_id


def test_resolve_id__with_plugin_definition() -> None:
    plugin_id = "my-first-plugin-id"
    assert resolve_id(PluginDefinition(plugin_id)) == plugin_id


def test_resolve_id__with_plugin_id() -> None:
    plugin_id = "my-first-plugin-id"
    assert resolve_id(plugin_id) == plugin_id
