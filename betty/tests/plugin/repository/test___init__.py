from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.plugin.error import PluginNotFound
from betty.plugin.repository import PluginRepository
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.machine_name import MachineName


class TestPluginRepository:
    class _Sut(PluginRepository[DummyPluginDefinition]):
        def __init__(self, *plugins: DummyPluginDefinition):
            super().__init__(DummyPluginDefinition)
            self._plugins = {plugin.id: plugin for plugin in plugins}

        @override
        def get(self, plugin_id: MachineName, /) -> DummyPluginDefinition:
            try:
                return self._plugins[plugin_id]
            except KeyError:
                raise PluginNotFound(
                    DummyPluginDefinition.type, plugin_id, []
                ) from None

        @override
        def __iter__(self) -> Iterator[DummyPluginDefinition]:
            yield from self._plugins.values()

    def test_type(self) -> None:
        assert self._Sut().type is DummyPluginDefinition

    def test___len__(self) -> None:
        sut = self._Sut(
            DummyPluginOne.plugin, DummyPluginTwo.plugin, DummyPluginThree.plugin
        )
        assert len(sut) == 3

    def test___getitem__(self) -> None:
        sut = self._Sut(DummyPluginOne.plugin)
        assert sut[DummyPluginOne.plugin.id] is DummyPluginOne.plugin

    def test_plugin_id_schema(self) -> None:
        sut = self._Sut(
            DummyPluginOne.plugin, DummyPluginTwo.plugin, DummyPluginThree.plugin
        )
        actual = sut.plugin_id_schema
        assert actual.schema["enum"] == [
            "dummy-plugin-one",
            "dummy-plugin-two",
            "dummy-plugin-three",
        ]
