import pytest

from betty.plugin.error import PluginNotFound
from betty.plugin.repository.static import StaticPluginRepository
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne


class TestStaticPluginRepository:
    def test_get(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition, DummyPluginOne)
        assert sut[DummyPluginOne.plugin().id] is DummyPluginOne.plugin()

    def test_get_not_found(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition)
        with pytest.raises(PluginNotFound):
            sut.get(DummyPluginOne.plugin().id)

    def test___iter__(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition, DummyPluginOne)
        plugin = list(iter(sut))[0]
        assert plugin is DummyPluginOne.plugin()

    def test___iter___without_plugins(self) -> None:
        sut = StaticPluginRepository(DummyPluginDefinition)
        with pytest.raises(StopIteration):
            next(iter(sut))
