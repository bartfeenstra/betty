from importlib.metadata import EntryPoint, EntryPoints

import pytest
from pytest_mock import MockerFixture

from betty.plugin import PluginUnavailable
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.test_utils.plugin import ClassedDummyPluginDefinition, ClassedDummyPluginOne


class TestEntryPointPluginRepository:
    def test_get(self, mocker: MockerFixture) -> None:
        entry_point_group = "test-entry-point"
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints(
                [
                    EntryPoint(
                        name=ClassedDummyPluginOne.plugin.id,
                        value="betty.test_utils.plugin:ClassedDummyPluginOne.plugin",
                        group=entry_point_group,
                    ),
                    EntryPoint(
                        name=ClassedDummyPluginOne.plugin.id,
                        value="betty.test_utils.plugin:ClassedDummyPluginTwo",
                        group=entry_point_group,
                    ),
                ]
            ),
        )
        sut = EntryPointPluginRepository(
            ClassedDummyPluginDefinition, entry_point_group
        )
        # Hit the cache.
        for _ in range(2):
            assert sut[ClassedDummyPluginOne.plugin.id] is ClassedDummyPluginOne.plugin
        m_entry_points.assert_called_once_with(group=entry_point_group)

    def test_get_not_found(self) -> None:
        sut = EntryPointPluginRepository(
            ClassedDummyPluginDefinition, "test-entry-point"
        )
        # Hit the cache.
        for _ in range(2):
            with pytest.raises(PluginUnavailable):
                sut.get(ClassedDummyPluginOne.plugin.id)

    def test___aiter___with_plugins(self, mocker: MockerFixture) -> None:
        entry_point_group = "test-entry-point"
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints(
                [
                    EntryPoint(
                        name=ClassedDummyPluginOne.plugin.id,
                        value="betty.test_utils.plugin:ClassedDummyPluginOne.plugin",
                        group=entry_point_group,
                    ),
                    EntryPoint(
                        name=ClassedDummyPluginOne.plugin.id,
                        value="betty.test_utils.plugin:ClassedDummyPluginTwo",
                        group=entry_point_group,
                    ),
                ]
            ),
        )
        sut = EntryPointPluginRepository(
            ClassedDummyPluginDefinition, entry_point_group
        )
        # Hit the cache.
        for _ in range(2):
            plugin = list(sut)[0]
            assert plugin is ClassedDummyPluginOne.plugin
        m_entry_points.assert_called_once_with(group=entry_point_group)

    def test___iter___without_plugins(self, mocker: MockerFixture) -> None:
        entry_point_group = "test-entry-point"
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints([]),
        )
        sut = EntryPointPluginRepository(
            ClassedDummyPluginDefinition, entry_point_group
        )
        # Hit the cache.
        for _ in range(2):
            with pytest.raises(StopIteration):
                next(iter(sut))
        m_entry_points.assert_called_once_with(group=entry_point_group)
