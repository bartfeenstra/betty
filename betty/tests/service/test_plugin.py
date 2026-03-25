from collections.abc import Iterable, Iterator, Mapping
from importlib.metadata import EntryPoint, EntryPoints
from typing import override

import pytest
from pytest_mock import MockerFixture

from betty.app import App
from betty.importlib import fully_qualified_name
from betty.machine_name import MachineName
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.discovery import ResolvableDiscovery
from betty.plugin.error import PluginNotFound
from betty.plugin.factory import PluginManufacturer
from betty.plugin.ordered import OrderedPluginDefinition
from betty.requirement import ServicePluginRequirement
from betty.service.level import ServiceLevel
from betty.service.level.universe import UNIVERSE
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
    def test_requires(self) -> None:
        requires = list(
            ServicePluginDefinition(
                "my-first-plugin-id", requires={DummyServicePluginIsolated}
            ).requires
        )
        assert len(requires) == 1
        assert isinstance(requires[0], ServicePluginRequirement)
        assert requires[0].plugin is DummyServicePluginIsolated

    def test_auto(self) -> None:
        assert ServicePluginDefinition("my-first-plugin-id", auto=True).auto
        assert not ServicePluginDefinition("my-first-plugin-id", auto=False).auto


class DummyServicePlugin(Plugin["DummyServicePluginDefinition"]):
    pass


@PluginTypeDefinition(
    "dummy-service-plugin",
    label="dummy service plugin",
    label_plural="dummy service plugin",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyServicePluginDefinition(ServicePluginDefinition[DummyServicePlugin]):
    pass


class DummyServicePluginManufacturer(
    PluginManufacturer[DummyServicePluginDefinition, DummyServicePlugin]
):
    @override
    @classmethod
    def plugin_type(cls) -> type[DummyServicePluginDefinition]:
        return DummyServicePluginDefinition


@DummyServicePluginDefinition("dummy-service-plugin-isolated")
class DummyServicePluginIsolated(DummyServicePlugin):
    pass


@DummyServicePluginDefinition(
    "dummy-service-plugin-requires-isolated", requires={DummyServicePluginIsolated}
)
class DummyServicePluginRequiresIsolated(DummyServicePlugin):
    pass


class DummyServicePluginRequirement(Plugin["DummyServicePluginRequirementDefinition"]):
    pass


@PluginTypeDefinition(
    "dummy-service-plugin-requirement",
    label="dummy service plugin requirement",
    label_plural="dummy service plugin requirement",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyServicePluginRequirementDefinition(
    ServicePluginDefinition[DummyServicePluginRequirement]
):
    pass


class DummyServicePluginRequirementManufacturer(
    PluginManufacturer[
        DummyServicePluginRequirementDefinition, DummyServicePluginRequirement
    ]
):
    @override
    @classmethod
    def plugin_type(cls) -> type[DummyServicePluginRequirementDefinition]:
        return DummyServicePluginRequirementDefinition


@DummyServicePluginRequirementDefinition(
    "dummy-service-plugin-requirement-requires-requires-isolated",
    requires={DummyServicePluginRequiresIsolated},
)
class DummyServicePluginRequirementRequiresRequiresIsolated(
    DummyServicePluginRequirement
):
    pass


class DummyServicePluginOrdered(Plugin["DummyServicePluginOrderedDefinition"]):
    pass


@PluginTypeDefinition(
    "dummy-service-plugin-ordered",
    label="dummy service plugin ordered",
    label_plural="dummy service plugin ordered",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyServicePluginOrderedDefinition(
    OrderedPluginDefinition, ServicePluginDefinition[DummyServicePluginOrdered]
):
    pass


class DummyServicePluginOrderedManufacturer(
    PluginManufacturer[DummyServicePluginOrderedDefinition, DummyServicePluginOrdered]
):
    @override
    @classmethod
    def plugin_type(cls) -> type[DummyServicePluginOrderedDefinition]:
        return DummyServicePluginOrderedDefinition


@DummyServicePluginOrderedDefinition("dummy-service-plugin-ordered-isolated")
class DummyServicePluginOrderedIsolated(DummyServicePluginOrdered):
    pass


@DummyServicePluginOrderedDefinition(
    "dummy-service-plugin-ordered-before-isolated",
    before={DummyServicePluginOrderedIsolated},
)
class DummyServicePluginOrderedBeforeIsolated(DummyServicePluginOrdered):
    pass


@DummyServicePluginOrderedDefinition(
    "dummy-service-plugin-ordered-after-isolated",
    after={DummyServicePluginOrderedIsolated},
)
class DummyServicePluginOrderedAfterIsolated(DummyServicePluginOrdered):
    pass


class DummyServicePluginAuto(Plugin["DummyServicePluginAutoDefinition"]):
    pass


@PluginTypeDefinition(
    "dummy-service-plugin-auto",
    label="dummy service plugin auto",
    label_plural="dummy service plugin auto",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyServicePluginAutoDefinition(ServicePluginDefinition[DummyServicePluginAuto]):
    pass


class DummyServicePluginAutoManufacturer(
    PluginManufacturer[DummyServicePluginAutoDefinition, DummyServicePluginAuto]
):
    @override
    @classmethod
    def plugin_type(cls) -> type[DummyServicePluginAutoDefinition]:
        return DummyServicePluginAutoDefinition


@DummyServicePluginAutoDefinition("dummy-service-plugin-auto-isolated", auto=True)
class DummyServicePluginAutoIsolated(DummyServicePluginAuto):
    pass


class TestServicePluginManager:
    @pytest.mark.parametrize(
        "key",
        [
            DummyServicePluginDefinition,
            DummyServicePluginDefinition.type().id,
        ],
    )
    async def test___getitem__(self, key: type[ServicePluginDefinition] | str) -> None:
        async with ServicePluginManager(
            {
                DummyServicePluginDefinition: [
                    DummyServicePluginManufacturer(DummyServicePluginIsolated)
                ]
            },
            services=ServiceLevel(
                plugins={DummyServicePluginDefinition: [DummyServicePluginIsolated]}
            ),
        ) as sut:
            assert isinstance(
                sut[key][DummyServicePluginIsolated],
                DummyServicePluginIsolated,
            )

    async def test___iter__(self) -> None:
        async with ServicePluginManager(
            {
                DummyServicePluginDefinition: [
                    DummyServicePluginManufacturer(DummyServicePluginIsolated)
                ]
            },
            services=ServiceLevel(
                plugins={DummyServicePluginDefinition: [DummyServicePluginIsolated]}
            ),
        ) as sut:
            assert list(iter(sut)) == [DummyServicePluginDefinition]

    @pytest.mark.parametrize(
        ("expected", "plugins", "service_plugins"),
        [
            # No service plugins.
            ({}, None, None),
            # A single, isolated service plugin.
            (
                {
                    DummyServicePluginDefinition: [
                        DummyServicePluginIsolated.plugin().id
                    ]
                },
                {DummyServicePluginDefinition: [DummyServicePluginIsolated]},
                {
                    DummyServicePluginDefinition: [
                        DummyServicePluginManufacturer(DummyServicePluginIsolated)
                    ]
                },
            ),
            # Two explicitly enabled service plugins of the same type, one dependent on the other.
            (
                {
                    DummyServicePluginDefinition: [
                        DummyServicePluginIsolated.plugin().id,
                        DummyServicePluginRequiresIsolated.plugin().id,
                    ]
                },
                {
                    DummyServicePluginDefinition: [
                        DummyServicePluginIsolated,
                        DummyServicePluginRequiresIsolated,
                    ]
                },
                {
                    DummyServicePluginDefinition: [
                        DummyServicePluginManufacturer(DummyServicePluginIsolated),
                        DummyServicePluginManufacturer(
                            DummyServicePluginRequiresIsolated
                        ),
                    ]
                },
            ),
            # One explicitly enabled service plugin, dependent on another of the same type.
            (
                {
                    DummyServicePluginDefinition: [
                        DummyServicePluginIsolated.plugin().id,
                        DummyServicePluginRequiresIsolated.plugin().id,
                    ]
                },
                {
                    DummyServicePluginDefinition: [
                        DummyServicePluginIsolated,
                        DummyServicePluginRequiresIsolated,
                    ]
                },
                {
                    DummyServicePluginDefinition: [
                        DummyServicePluginManufacturer(
                            DummyServicePluginRequiresIsolated
                        ),
                    ]
                },
            ),
            # One explicitly enabled service plugin, with nested dependencies across different plugin types.
            (
                {
                    DummyServicePluginDefinition: [
                        DummyServicePluginIsolated.plugin().id,
                        DummyServicePluginRequiresIsolated.plugin().id,
                    ],
                    DummyServicePluginRequirementDefinition: [
                        DummyServicePluginRequirementRequiresRequiresIsolated.plugin().id,
                    ],
                },
                {
                    DummyServicePluginDefinition: [
                        DummyServicePluginIsolated,
                        DummyServicePluginRequiresIsolated,
                    ],
                    DummyServicePluginRequirementDefinition: [
                        DummyServicePluginRequirementRequiresRequiresIsolated,
                    ],
                },
                {
                    DummyServicePluginRequirementDefinition: [
                        DummyServicePluginRequirementManufacturer(
                            DummyServicePluginRequirementRequiresRequiresIsolated
                        ),
                    ]
                },
            ),
            # Ordered plugins.
            (
                {
                    DummyServicePluginOrderedDefinition: [
                        DummyServicePluginOrderedBeforeIsolated.plugin().id,
                        DummyServicePluginOrderedIsolated.plugin().id,
                        DummyServicePluginOrderedAfterIsolated.plugin().id,
                    ],
                },
                {
                    DummyServicePluginOrderedDefinition: [
                        DummyServicePluginOrderedAfterIsolated,
                        DummyServicePluginOrderedIsolated,
                        DummyServicePluginOrderedBeforeIsolated,
                    ],
                },
                {
                    DummyServicePluginOrderedDefinition: [
                        DummyServicePluginOrderedManufacturer(
                            DummyServicePluginOrderedAfterIsolated
                        ),
                        DummyServicePluginOrderedManufacturer(
                            DummyServicePluginOrderedIsolated
                        ),
                        DummyServicePluginOrderedManufacturer(
                            DummyServicePluginOrderedBeforeIsolated
                        ),
                    ]
                },
            ),
            # Auto service plugins.
            (
                {
                    DummyServicePluginAutoDefinition: [
                        DummyServicePluginAutoIsolated.plugin().id,
                    ],
                },
                {
                    DummyServicePluginAutoDefinition: [
                        DummyServicePluginAutoIsolated,
                    ],
                },
                {
                    DummyServicePluginAutoDefinition: [],
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
