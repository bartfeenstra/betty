import pytest

from betty.plugin import PluginUnavailable
from betty.plugin.static import StaticPluginRepository
from betty.test_utils.plugin import DUMMY_PLUGIN_ONE, DummyPluginDefinition


class TestStaticPluginRepository:
    def test_get(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition, DUMMY_PLUGIN_ONE)
        assert sut[DUMMY_PLUGIN_ONE.id] is DUMMY_PLUGIN_ONE

    def test_get_not_found(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition)
        with pytest.raises(PluginUnavailable):
            sut.get(DUMMY_PLUGIN_ONE.id)

    def test___iter__(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition, DUMMY_PLUGIN_ONE)
        plugin = list(iter(sut))[0]
        assert plugin is DUMMY_PLUGIN_ONE

    def test___iter___without_plugins(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition)
        with pytest.raises(StopIteration):
            next(iter(sut))
