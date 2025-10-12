from importlib.metadata import EntryPoint, EntryPoints

import pytest
from pytest_mock import MockerFixture

from betty.plugin import PluginNotFound
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.test_utils.plugin import DUMMY_PLUGIN_ONE, DummyPluginDefinition


class TestEntryPointPluginRepository:
    def test_get(self, mocker: MockerFixture) -> None:
        entry_point_group = "test-entry-point"
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints(
                [
                    EntryPoint(
                        name=DUMMY_PLUGIN_ONE.id,
                        value="betty.test_utils.plugin:DUMMY_PLUGIN_ONE",
                        group=entry_point_group,
                    )
                ]
            ),
        )
        sut = EntryPointPluginRepository(DummyPluginDefinition, entry_point_group)
        # Hit the cache.
        for _ in range(2):
            assert sut[DUMMY_PLUGIN_ONE.id] is DUMMY_PLUGIN_ONE
        m_entry_points.assert_called_once_with(group=entry_point_group)

    def test_get_not_found(self) -> None:
        sut = EntryPointPluginRepository(DummyPluginDefinition, "test-entry-point")
        # Hit the cache.
        for _ in range(2):
            with pytest.raises(PluginNotFound):
                sut.get(DUMMY_PLUGIN_ONE.id)

    def test___aiter___with_plugins(self, mocker: MockerFixture) -> None:
        entry_point_group = "test-entry-point"
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints(
                [
                    EntryPoint(
                        name=DUMMY_PLUGIN_ONE.id,
                        value="betty.test_utils.plugin:DUMMY_PLUGIN_ONE",
                        group=entry_point_group,
                    )
                ]
            ),
        )
        sut = EntryPointPluginRepository(DummyPluginDefinition, entry_point_group)
        # Hit the cache.
        for _ in range(2):
            plugin = list(sut)[0]
            assert plugin is DUMMY_PLUGIN_ONE
        m_entry_points.assert_called_once_with(group=entry_point_group)

    def test___iter___without_plugins(self, mocker: MockerFixture) -> None:
        entry_point_group = "test-entry-point"
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints([]),
        )
        sut = EntryPointPluginRepository(DummyPluginDefinition, entry_point_group)
        # Hit the cache.
        for _ in range(2):
            with pytest.raises(StopIteration):
                next(iter(sut))
        m_entry_points.assert_called_once_with(group=entry_point_group)
