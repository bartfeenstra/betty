import pytest

from betty.plugin import PluginNotFound
from betty.plugin.proxy import ProxyPluginRepository
from betty.plugin.static import StaticPluginRepository
from betty.test_utils.plugin import (
    DUMMY_PLUGIN_ONE,
    DUMMY_PLUGIN_THREE,
    DUMMY_PLUGIN_TWO,
    DummyPluginDefinition,
)


class TestProxyPluginRepository:
    def test_get(self) -> None:
        sut = ProxyPluginRepository(
            DummyPluginDefinition,
            StaticPluginRepository(DummyPluginDefinition, DUMMY_PLUGIN_ONE),
        )
        assert sut[DUMMY_PLUGIN_ONE.id] is DUMMY_PLUGIN_ONE

    def test_get__not_found_without_upstreams(self) -> None:
        sut = ProxyPluginRepository(DummyPluginDefinition)
        with pytest.raises(PluginNotFound):
            sut.get(DUMMY_PLUGIN_ONE.id)

    def test_get__not_found_with_upstreams(self) -> None:
        sut = ProxyPluginRepository(
            DummyPluginDefinition,
            StaticPluginRepository(DummyPluginDefinition, DUMMY_PLUGIN_ONE),
            StaticPluginRepository(DummyPluginDefinition, DUMMY_PLUGIN_TWO),
        )
        with pytest.raises(PluginNotFound):
            sut.get(DUMMY_PLUGIN_THREE.id)

    def test___iter____without_upstreams(self) -> None:
        sut = ProxyPluginRepository(DummyPluginDefinition)
        with pytest.raises(StopIteration):
            next(iter(sut))

    def test___iter____with_upstreams_without_plugins(self) -> None:
        sut = ProxyPluginRepository(
            DummyPluginDefinition,
            StaticPluginRepository(DummyPluginDefinition),
            StaticPluginRepository(DummyPluginDefinition),
            StaticPluginRepository(DummyPluginDefinition),
        )
        with pytest.raises(StopIteration):
            next(iter(sut))

    def test___iter____with_upstreams_with_plugins(self) -> None:
        sut = ProxyPluginRepository(
            DummyPluginDefinition,
            StaticPluginRepository(DummyPluginDefinition, DUMMY_PLUGIN_ONE),
            StaticPluginRepository(
                DummyPluginDefinition,
                DUMMY_PLUGIN_TWO,
                DUMMY_PLUGIN_ONE,
            ),
            StaticPluginRepository(
                DummyPluginDefinition,
                DUMMY_PLUGIN_THREE,
                DUMMY_PLUGIN_TWO,
                DUMMY_PLUGIN_ONE,
            ),
        )
        actual = list(iter(sut))
        assert actual == [
            DUMMY_PLUGIN_ONE,
            DUMMY_PLUGIN_TWO,
            DUMMY_PLUGIN_THREE,
        ]
