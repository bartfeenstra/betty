from importlib.metadata import EntryPoints, EntryPoint

import pytest
from pytest_mock import MockerFixture

from betty.locale.localizable import Localizable, plain
from betty.plugin import Plugin, PluginNotFound
from betty.machine_name import MachineName
from betty.plugin.entry_point import EntryPointPluginRepository


class EntryPointPluginRepositoryTestPlugin(Plugin):
    @classmethod
    def plugin_id(cls) -> MachineName:
        return cls.__name__

    @classmethod
    def plugin_label(cls) -> Localizable:
        return plain("")  # pragma: no cover


class TestEntryPointPluginRepository:
    async def test_get(self, mocker: MockerFixture) -> None:
        entry_point_group = "test-entry-point"
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints(
                [
                    EntryPoint(
                        name=EntryPointPluginRepositoryTestPlugin.plugin_id(),
                        value=f"{EntryPointPluginRepositoryTestPlugin.__module__}:{EntryPointPluginRepositoryTestPlugin.__qualname__}",
                        group=entry_point_group,
                    )
                ]
            ),
        )
        sut = EntryPointPluginRepository[Plugin](entry_point_group)
        # Hit the cache.
        for _ in range(0, 2):
            await sut.get(EntryPointPluginRepositoryTestPlugin.plugin_id())
        m_entry_points.assert_called_once_with(group=entry_point_group)

    async def test_get_not_found(self) -> None:
        sut = EntryPointPluginRepository[Plugin]("test-entry-point")
        # Hit the cache.
        for _ in range(0, 2):
            with pytest.raises(PluginNotFound):
                await sut.get(EntryPointPluginRepositoryTestPlugin.plugin_id())

    async def test___aiter___with_plugins(self, mocker: MockerFixture) -> None:
        entry_point_group = "test-entry-point"
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints(
                [
                    EntryPoint(
                        name=EntryPointPluginRepositoryTestPlugin.plugin_id(),
                        value=f"{EntryPointPluginRepositoryTestPlugin.__module__}:{EntryPointPluginRepositoryTestPlugin.__qualname__}",
                        group=entry_point_group,
                    )
                ]
            ),
        )
        sut = EntryPointPluginRepository[Plugin](entry_point_group)
        # Hit the cache.
        for _ in range(0, 2):
            plugin = await anext(aiter(sut))
            assert plugin is EntryPointPluginRepositoryTestPlugin
        m_entry_points.assert_called_once_with(group=entry_point_group)

    async def test___aiter___without_plugins(self, mocker: MockerFixture) -> None:
        entry_point_group = "test-entry-point"
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints([]),
        )
        sut = EntryPointPluginRepository[Plugin](entry_point_group)
        # Hit the cache.
        for _ in range(0, 2):
            with pytest.raises(StopAsyncIteration):
                await anext(aiter(sut))
        m_entry_points.assert_called_once_with(group=entry_point_group)
