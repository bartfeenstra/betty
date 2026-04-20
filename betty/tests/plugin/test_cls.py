from betty.plugin.cls import Plugin, PluginClsDefinition


class TestPluginClsDefinition:
    def test__set_cls__without_plugin_class(self) -> None:
        class _Plugin:
            pass

        sut = PluginClsDefinition("-")
        sut(_Plugin)
        assert sut.cls is _Plugin
        assert not hasattr(_Plugin, "plugin")

    def test__set_cls__with_plugin_class(self) -> None:
        class _Plugin(Plugin):
            pass

        sut = PluginClsDefinition("-")
        sut(_Plugin)
        assert sut.cls is _Plugin
        assert _Plugin.plugin() is sut
