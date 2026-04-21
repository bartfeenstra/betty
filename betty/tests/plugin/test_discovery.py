from __future__ import annotations

from importlib.metadata import EntryPoint, EntryPoints
from typing import TYPE_CHECKING

import pytest

from betty.importlib import fully_qualified_name
from betty.plugin.discovery import PluginDiscoverer, ResolvableDiscovery, discover
from betty.plugin.error import PluginNotFound
from betty.service_level import ServiceLevel
from betty.string import kebab_case_to_snake_case
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Iterator, Set

    from pytest_mock import MockerFixture


def _new_static_discovery_sync(
    *discoveries: ResolvableDiscovery[DummyPluginDefinition],
) -> Callable[[ServiceLevel], Iterable[ResolvableDiscovery[DummyPluginDefinition]]]:
    def _static_discovery_sync(
        services: ServiceLevel,
    ) -> Iterable[ResolvableDiscovery[DummyPluginDefinition]]:
        return discoveries

    return _static_discovery_sync


def _new_static_discovery_async(
    *discoveries: ResolvableDiscovery[DummyPluginDefinition],
) -> Callable[
    [ServiceLevel],
    Awaitable[Iterable[ResolvableDiscovery[DummyPluginDefinition]]],
]:
    async def _static_discovery_async(
        services: ServiceLevel,
    ) -> Iterable[ResolvableDiscovery[DummyPluginDefinition]]:
        return discoveries

    return _static_discovery_async


@pytest.mark.parametrize(
    ("expected", "discoveries"),
    [
        (set(), []),
        ({DummyPluginOne.plugin()}, [DummyPluginOne]),
        ({DummyPluginOne.plugin()}, [DummyPluginOne.plugin()]),
        ({DummyPluginOne.plugin()}, [_new_static_discovery_sync(DummyPluginOne)]),
        (
            {DummyPluginOne.plugin()},
            [_new_static_discovery_sync(DummyPluginOne.plugin())],
        ),
        ({DummyPluginOne.plugin()}, [_new_static_discovery_async(DummyPluginOne)]),
        (
            {DummyPluginOne.plugin()},
            [_new_static_discovery_async(DummyPluginOne.plugin())],
        ),
    ],
)
async def test_discover(
    expected: Set[DummyPluginDefinition],
    discoveries: Iterable[ResolvableDiscovery[DummyPluginDefinition]],
) -> None:
    assert set(await discover(ServiceLevel(), *discoveries)) == expected


class TestPluginDiscoverer:
    @pytest.fixture
    def entry_points(self, mocker: MockerFixture) -> Iterator[None]:
        entry_point_group = kebab_case_to_snake_case(DummyPluginDefinition.type().id)
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints([
                EntryPoint(
                    name=DummyPluginOne.plugin().id,
                    value=fully_qualified_name(DummyPluginOne),
                    group=entry_point_group,
                ),
            ]),
        )
        yield
        m_entry_points.assert_called_once_with(group=f"betty.{entry_point_group}")

    async def test___aiter____without_plugins(self) -> None:
        sut = PluginDiscoverer(ServiceLevel(), DummyPluginDefinition, [])
        assert not [x async for x in aiter(sut)]

    async def test___aiter____with_discovered_plugins(self, entry_points: None) -> None:
        sut = PluginDiscoverer(ServiceLevel(), DummyPluginDefinition)
        assert DummyPluginOne.plugin() in [x async for x in aiter(sut)]

    async def test___aiter____with_overridden_plugins(self) -> None:
        sut = PluginDiscoverer(ServiceLevel(), DummyPluginDefinition, [DummyPluginOne])
        assert [x async for x in aiter(sut)] == [DummyPluginOne.plugin()]

    async def test_get__with_plugin_not_found(self) -> None:
        sut = PluginDiscoverer(ServiceLevel(), DummyPluginDefinition, [])
        with pytest.raises(PluginNotFound):
            await sut.get("unknown-plugin")

    async def test_get__with_discovered_plugins(self, entry_points: None) -> None:
        sut = PluginDiscoverer(ServiceLevel(), DummyPluginDefinition)
        assert await sut.get(DummyPluginOne.plugin().id) is DummyPluginOne.plugin()

    async def test_get__with_overridden_plugin(self) -> None:
        sut = PluginDiscoverer(ServiceLevel(), DummyPluginDefinition, [DummyPluginOne])
        assert await sut.get(DummyPluginOne.plugin().id) is DummyPluginOne.plugin()

    async def test___getitem__(self, entry_points: None) -> None:
        sut = PluginDiscoverer(ServiceLevel(), DummyPluginDefinition)
        assert await sut[DummyPluginOne.plugin().id] is DummyPluginOne.plugin()

    async def test_ids__without_plugins(self) -> None:
        sut = PluginDiscoverer(ServiceLevel(), DummyPluginDefinition, [])
        assert not list(await sut.ids())

    async def test_ids__with_discovered_plugins(self, entry_points: None) -> None:
        sut = PluginDiscoverer(ServiceLevel(), DummyPluginDefinition)
        assert DummyPluginOne.plugin().id in list(await sut.ids())

    async def test_ids__with_overridden_plugins(self) -> None:
        sut = PluginDiscoverer(ServiceLevel(), DummyPluginDefinition, [DummyPluginOne])
        assert list(await sut.ids()) == [DummyPluginOne.plugin().id]

    def test_type(self) -> None:
        sut = PluginDiscoverer(ServiceLevel(), DummyPluginDefinition)
        assert sut.type is DummyPluginDefinition
