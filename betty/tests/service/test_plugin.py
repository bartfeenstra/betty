import builtins
from collections.abc import Iterable, Iterator, Mapping, Sequence
from importlib.metadata import EntryPoint, EntryPoints
from typing import override

import pytest
from pytest_mock import MockerFixture

from betty.app import App
from betty.importlib import fully_qualified_name
from betty.machine_name import MachineName
from betty.plugin import (
    Plugin,
    PluginDefinition,
    PluginTypeDefinition,
    ResolvablePluginId,
)
from betty.plugin.discovery import ResolvableDiscovery
from betty.plugin.error import PluginNotFound
from betty.plugin.factory import PluginManufacturer
from betty.plugin.ordered import OrderedPluginDefinition
from betty.service.level import UNIVERSE, ServiceLevel
from betty.service.plugin import (
    PluginCollection,
    PluginManager,
    ServicePluginDefinition,
    ServicePluginManager,
    ServicePluginManufacturers,
)
from betty.string import kebab_case_to_snake_case
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginFour,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
)


class TestPluginCollection:
    PLUGIN_ONE = DummyPluginOne()
    PLUGIN_TWO = DummyPluginTwo()
    PLUGIN_THREE = DummyPluginThree()
    PLUGIN_FOUR = DummyPluginFour()

    def test___contains____without_plugins(self) -> None:
        sut = PluginCollection([])
        assert DummyPluginOne not in sut

    def test___contains____with_unknown_plugin(self) -> None:
        sut = PluginCollection([[]])
        assert DummyPluginOne not in sut

    def test___contains____with_known_plugin(self) -> None:
        sut = PluginCollection([[self.PLUGIN_ONE]])
        assert DummyPluginOne in sut

    def test___contains____with_invalid_value(self) -> None:
        sut = PluginCollection([])
        assert object() not in sut

    def test___getitem____without_plugins(self) -> None:
        sut = PluginCollection([])
        with pytest.raises(KeyError):
            sut[DummyPluginOne]

    def test___getitem____with_unknown_plugin(self) -> None:
        sut = PluginCollection([[]])
        with pytest.raises(KeyError):
            sut[DummyPluginOne]

    def test___getitem____with_known_plugin(self) -> None:
        sut = PluginCollection([[DummyPluginOne()]])
        sut[DummyPluginOne]

    @pytest.mark.parametrize(
        ("expected", "plugins"),
        [
            ([], []),
            ([PLUGIN_ONE], [[PLUGIN_ONE]]),
            (
                [
                    PLUGIN_ONE,
                    PLUGIN_TWO,
                    PLUGIN_THREE,
                    PLUGIN_FOUR,
                ],
                [
                    [PLUGIN_ONE, PLUGIN_TWO],
                    [PLUGIN_THREE, PLUGIN_FOUR],
                ],
            ),
        ],
    )
    def test___iter__(
        self, expected: list[Plugin], plugins: Iterable[Iterable[Plugin]]
    ) -> None:
        assert list(iter(PluginCollection(plugins))) == expected

    @pytest.mark.parametrize(
        ("expected", "plugins"),
        [
            (0, []),
            (1, [[DummyPluginOne()]]),
            (
                4,
                [
                    [DummyPluginOne(), DummyPluginTwo()],
                    [DummyPluginThree(), DummyPluginFour()],
                ],
            ),
        ],
    )
    def test___len__(self, expected: int, plugins: Iterable[Iterable[Plugin]]) -> None:
        assert len(PluginCollection(plugins)) == expected

    @pytest.mark.parametrize(
        ("expected", "plugins"),
        [
            ([], []),
            ([DummyPluginOne.plugin().id], [[DummyPluginOne()]]),
            (
                [
                    DummyPluginOne.plugin().id,
                    DummyPluginTwo.plugin().id,
                    DummyPluginThree.plugin().id,
                    DummyPluginFour.plugin().id,
                ],
                [
                    [DummyPluginOne(), DummyPluginTwo()],
                    [DummyPluginThree(), DummyPluginFour()],
                ],
            ),
        ],
    )
    def test_keys(
        self, expected: list[MachineName], plugins: Iterable[Iterable[Plugin]]
    ) -> None:
        assert list(PluginCollection(plugins).keys()) == expected


class TestPluginManager:
    @pytest.fixture
    def entry_points(self, mocker: MockerFixture) -> Iterator[None]:
        entry_point_group = kebab_case_to_snake_case(DummyPluginDefinition.type().id)
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints(
                [
                    EntryPoint(
                        name=DummyPluginOne.plugin().id,
                        value=fully_qualified_name(DummyPluginOne),
                        group=entry_point_group,
                    ),
                ]
            ),
        )
        yield
        m_entry_points.assert_called_once_with(group=f"betty.{entry_point_group}")

    async def test___aiter____without_plugins(self) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition, [])
        assert not [x async for x in aiter(sut)]

    async def test___aiter____with_discovered_plugins(self, entry_points: None) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition)
        assert DummyPluginOne.plugin() in [x async for x in aiter(sut)]

    async def test___aiter____with_overridden_plugins(self) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition, [DummyPluginOne])
        assert [x async for x in aiter(sut)] == [DummyPluginOne.plugin()]

    async def test___getitem____with_plugin_not_found(self) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition, [])
        with pytest.raises(PluginNotFound):
            await sut["unknown-plugin"]

    async def test___getitem____with_discovered_plugins(
        self, entry_points: None
    ) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition)
        assert await sut[DummyPluginOne.plugin().id] is DummyPluginOne.plugin()

    async def test___getitem____with_overridden_plugin(self) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition, [DummyPluginOne])
        assert await sut[DummyPluginOne.plugin().id] is DummyPluginOne.plugin()

    async def test_ids__without_plugins(self) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition, [])
        assert not list(await sut.ids())

    async def test_ids__with_discovered_plugins(self, entry_points: None) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition)
        assert DummyPluginOne.plugin().id in list(await sut.ids())

    async def test_ids__with_overridden_plugins(self) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition, [DummyPluginOne])
        assert list(await sut.ids()) == [DummyPluginOne.plugin().id]

    def test_type(self) -> None:
        sut = PluginManager(UNIVERSE, DummyPluginDefinition)
        assert sut.type is DummyPluginDefinition


class TestServicePluginDefinition:
    @pytest.mark.parametrize(
        ("expected", "requires"),
        [
            ({}, {}),
            ({DummyPluginDefinition: []}, {DummyPluginDefinition: {}}),
            (
                {DummyPluginDefinition: [DummyPluginOne.plugin().id]},
                {DummyPluginDefinition: DummyPluginOne},
            ),
            (
                {DummyPluginDefinition: [DummyPluginOne.plugin().id]},
                {DummyPluginDefinition: [DummyPluginOne]},
            ),
        ],
    )
    def test_requires(
        self,
        expected: Mapping[type[ServicePluginDefinition], Sequence[MachineName]],
        requires: Mapping[
            type[ServicePluginDefinition],
            ResolvablePluginId | Iterable[ResolvablePluginId],
        ]
        | None,
    ) -> None:
        assert (
            ServicePluginDefinition("my-first-plugin-id", requires=requires).requires
            == expected
        )


class DummyServicePluginAlpha(Plugin["DummyServicePluginAlphaDefinition"]):
    pass


@PluginTypeDefinition(
    "dummy-service-plugin-alpha",
    label="dummy service plugin alpha",
    label_plural="dummy service plugin alpha",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyServicePluginAlphaDefinition(
    ServicePluginDefinition[DummyServicePluginAlpha]
):
    pass


class DummyServicePluginAlphaManufacturer(
    PluginManufacturer[DummyServicePluginAlphaDefinition, DummyServicePluginAlpha]
):
    @override
    @classmethod
    def type(cls) -> builtins.type[DummyServicePluginAlphaDefinition]:
        return DummyServicePluginAlphaDefinition


@DummyServicePluginAlphaDefinition("dummy-service-plugin-alpha-isolated")
class DummyServicePluginAlphaIsolated(DummyServicePluginAlpha):
    pass


@DummyServicePluginAlphaDefinition(
    "dummy-service-plugin-alpha-requires-alpha-isolated",
    requires={DummyServicePluginAlphaDefinition: {DummyServicePluginAlphaIsolated}},
)
class DummyServicePluginAlphaRequiresAlphaIsolated(DummyServicePluginAlpha):
    pass


class DummyServicePluginBeta(Plugin["DummyServicePluginBetaDefinition"]):
    pass


@PluginTypeDefinition(
    "dummy-service-plugin-beta",
    label="dummy service plugin beta",
    label_plural="dummy service plugin beta",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyServicePluginBetaDefinition(ServicePluginDefinition[DummyServicePluginBeta]):
    pass


class DummyServicePluginBetaManufacturer(
    PluginManufacturer[DummyServicePluginBetaDefinition, DummyServicePluginBeta]
):
    @override
    @classmethod
    def type(cls) -> builtins.type[DummyServicePluginBetaDefinition]:
        return DummyServicePluginBetaDefinition


@DummyServicePluginBetaDefinition(
    "dummy-service-plugin-beta-requires-requires-alpha-isolated",
    requires={
        DummyServicePluginAlphaDefinition: {
            DummyServicePluginAlphaRequiresAlphaIsolated
        }
    },
)
class DummyServicePluginBetaRequiresRequiresAlphaIsolated(DummyServicePluginBeta):
    pass


class DummyServicePluginGamma(Plugin["DummyServicePluginGammaDefinition"]):
    pass


@PluginTypeDefinition(
    "dummy-service-plugin-gamma",
    label="dummy service plugin gamma",
    label_plural="dummy service plugin gamma",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyServicePluginGammaDefinition(
    OrderedPluginDefinition, ServicePluginDefinition[DummyServicePluginGamma]
):
    pass


class DummyServicePluginGammaManufacturer(
    PluginManufacturer[DummyServicePluginGammaDefinition, DummyServicePluginGamma]
):
    @override
    @classmethod
    def type(cls) -> builtins.type[DummyServicePluginGammaDefinition]:
        return DummyServicePluginGammaDefinition


@DummyServicePluginGammaDefinition("dummy-service-plugin-gamma-isolated")
class DummyServicePluginGammaIsolated(DummyServicePluginGamma):
    pass


@DummyServicePluginGammaDefinition(
    "dummy-service-plugin-gamma-comes-before-isolated",
    comes_before={DummyServicePluginGammaIsolated},
)
class DummyServicePluginGammaComesBeforeIsolated(DummyServicePluginGamma):
    pass


@DummyServicePluginGammaDefinition(
    "dummy-service-plugin-gamma-comes-after-isolated",
    comes_after={DummyServicePluginGammaIsolated},
)
class DummyServicePluginGammaComesAfterIsolated(DummyServicePluginGamma):
    pass


class TestServicePluginManager:
    @pytest.mark.parametrize(
        "key",
        [
            DummyServicePluginAlphaDefinition,
            DummyServicePluginAlphaDefinition.type().id,
        ],
    )
    async def test___getitem__(self, key: type[ServicePluginDefinition] | str) -> None:
        async with ServicePluginManager(
            {
                DummyServicePluginAlphaDefinition: [
                    DummyServicePluginAlphaManufacturer(DummyServicePluginAlphaIsolated)
                ]
            },
            services=ServiceLevel(
                plugins={
                    DummyServicePluginAlphaDefinition: [DummyServicePluginAlphaIsolated]
                }
            ),
        ) as sut:
            assert isinstance(
                sut[key][DummyServicePluginAlphaIsolated],
                DummyServicePluginAlphaIsolated,
            )

    async def test___iter__(self) -> None:
        async with ServicePluginManager(
            {
                DummyServicePluginAlphaDefinition: [
                    DummyServicePluginAlphaManufacturer(DummyServicePluginAlphaIsolated)
                ]
            },
            services=ServiceLevel(
                plugins={
                    DummyServicePluginAlphaDefinition: [DummyServicePluginAlphaIsolated]
                }
            ),
        ) as sut:
            assert list(iter(sut)) == [DummyServicePluginAlphaDefinition]

    @pytest.mark.parametrize(
        ("expected", "plugins", "service_plugins"),
        [
            # No service plugins.
            ({}, None, None),
            # A single, isolated service plugin.
            (
                {
                    DummyServicePluginAlphaDefinition: [
                        DummyServicePluginAlphaIsolated.plugin().id
                    ]
                },
                {DummyServicePluginAlphaDefinition: [DummyServicePluginAlphaIsolated]},
                {
                    DummyServicePluginAlphaDefinition: [
                        DummyServicePluginAlphaManufacturer(
                            DummyServicePluginAlphaIsolated
                        )
                    ]
                },
            ),
            # Two explicitly enabled service plugins of the same type, one dependent on the other.
            (
                {
                    DummyServicePluginAlphaDefinition: [
                        DummyServicePluginAlphaIsolated.plugin().id,
                        DummyServicePluginAlphaRequiresAlphaIsolated.plugin().id,
                    ]
                },
                {
                    DummyServicePluginAlphaDefinition: [
                        DummyServicePluginAlphaIsolated,
                        DummyServicePluginAlphaRequiresAlphaIsolated,
                    ]
                },
                {
                    DummyServicePluginAlphaDefinition: [
                        DummyServicePluginAlphaManufacturer(
                            DummyServicePluginAlphaIsolated
                        ),
                        DummyServicePluginAlphaManufacturer(
                            DummyServicePluginAlphaRequiresAlphaIsolated
                        ),
                    ]
                },
            ),
            # One explicitly enabled service plugin, dependent on another of the same type.
            (
                {
                    DummyServicePluginAlphaDefinition: [
                        DummyServicePluginAlphaIsolated.plugin().id,
                        DummyServicePluginAlphaRequiresAlphaIsolated.plugin().id,
                    ]
                },
                {
                    DummyServicePluginAlphaDefinition: [
                        DummyServicePluginAlphaIsolated,
                        DummyServicePluginAlphaRequiresAlphaIsolated,
                    ]
                },
                {
                    DummyServicePluginAlphaDefinition: [
                        DummyServicePluginAlphaManufacturer(
                            DummyServicePluginAlphaRequiresAlphaIsolated
                        ),
                    ]
                },
            ),
            # One explicitly enabled service plugin, with nested dependencies across different plugin types.
            (
                {
                    DummyServicePluginAlphaDefinition: [
                        DummyServicePluginAlphaIsolated.plugin().id,
                        DummyServicePluginAlphaRequiresAlphaIsolated.plugin().id,
                    ],
                    DummyServicePluginBetaDefinition: [
                        DummyServicePluginBetaRequiresRequiresAlphaIsolated.plugin().id,
                    ],
                },
                {
                    DummyServicePluginAlphaDefinition: [
                        DummyServicePluginAlphaIsolated,
                        DummyServicePluginAlphaRequiresAlphaIsolated,
                    ],
                    DummyServicePluginBetaDefinition: [
                        DummyServicePluginBetaRequiresRequiresAlphaIsolated,
                    ],
                },
                {
                    DummyServicePluginBetaDefinition: [
                        DummyServicePluginBetaManufacturer(
                            DummyServicePluginBetaRequiresRequiresAlphaIsolated
                        ),
                    ]
                },
            ),
            # Ordered plugins.
            (
                {
                    DummyServicePluginGammaDefinition: [
                        DummyServicePluginGammaComesBeforeIsolated.plugin().id,
                        DummyServicePluginGammaIsolated.plugin().id,
                        DummyServicePluginGammaComesAfterIsolated.plugin().id,
                    ],
                },
                {
                    DummyServicePluginGammaDefinition: [
                        DummyServicePluginGammaComesAfterIsolated,
                        DummyServicePluginGammaIsolated,
                        DummyServicePluginGammaComesBeforeIsolated,
                    ],
                },
                {
                    DummyServicePluginGammaDefinition: [
                        DummyServicePluginGammaManufacturer(
                            DummyServicePluginGammaComesAfterIsolated
                        ),
                        DummyServicePluginGammaManufacturer(
                            DummyServicePluginGammaIsolated
                        ),
                        DummyServicePluginGammaManufacturer(
                            DummyServicePluginGammaComesBeforeIsolated
                        ),
                    ]
                },
            ),
        ],
    )
    async def test_bootstrap(
        self,
        expected,
        plugins: Mapping[
            type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
        ]
        | None,
        service_plugins: ServicePluginManufacturers,
        isolated_app: App,
    ) -> None:
        async with ServicePluginManager(
            service_plugins, services=ServiceLevel(plugins=plugins)
        ) as sut:
            assert set(sut) == set(expected)
            for plugin_type in expected:
                assert [plugin.plugin().id for plugin in sut[plugin_type]] == expected[
                    plugin_type
                ]
