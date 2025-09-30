from importlib.metadata import EntryPoint, EntryPoints

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.locale.localizable import Localizable, StaticTranslations
from betty.machine_name import MachineName
from betty.plugin import Plugin, PluginNotFound
from betty.plugin.entry_point import EntryPointPluginRepository


class EntryPointPluginRepositoryTestPlugin(Plugin):
    @override
    @classmethod
    def plugin_id(cls) -> MachineName:
        return cls.__name__

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return StaticTranslations("")  # pragma: no cover


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
        sut = EntryPointPluginRepository(
            EntryPointPluginRepositoryTestPlugin, entry_point_group
        )
        # Hit the cache.
        for _ in range(2):
            await sut.get(EntryPointPluginRepositoryTestPlugin.plugin_id())
        m_entry_points.assert_called_once_with(group=entry_point_group)

    async def test_get_not_found(self) -> None:
        sut = EntryPointPluginRepository(
            EntryPointPluginRepositoryTestPlugin, "test-entry-point"
        )
        # Hit the cache.
        for _ in range(2):
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
        sut = EntryPointPluginRepository(
            EntryPointPluginRepositoryTestPlugin, entry_point_group
        )
        # Hit the cache.
        for _ in range(2):
            plugin = [plugin async for plugin in sut][0]
            assert plugin is EntryPointPluginRepositoryTestPlugin
        m_entry_points.assert_called_once_with(group=entry_point_group)

    async def test___aiter___without_plugins(self, mocker: MockerFixture) -> None:
        entry_point_group = "test-entry-point"
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints([]),
        )
        sut = EntryPointPluginRepository(
            EntryPointPluginRepositoryTestPlugin, entry_point_group
        )
        # Hit the cache.
        for _ in range(2):
            with pytest.raises(StopAsyncIteration):
                await anext(aiter(sut))
        m_entry_points.assert_called_once_with(group=entry_point_group)
