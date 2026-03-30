from collections.abc import Iterable, Mapping
from typing import override

import pytest

from betty.app import App
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.cls import Plugin
from betty.plugin.discovery import ResolvableDiscovery
from betty.plugin.factory import PluginManufacturer
from betty.plugin.ordered import OrderedPluginDefinition
from betty.service.level import ServiceLevel
from betty.service.plugin.service import (
    ServicePluginCollection,
    ServicePluginDefinition,
    ServicePluginManager,
    ServicePlugins,
    ServicePluginTypes,
    SupportPlugins,
)
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE
from betty.test_utils.plugin import (
    DummyPluginFour,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
)


class TestServicePluginCollection:
    PLUGIN_ONE = DummyPluginOne()
    PLUGIN_TWO = DummyPluginTwo()
    PLUGIN_THREE = DummyPluginThree()
    PLUGIN_FOUR = DummyPluginFour()

    def test___contains____without_plugins(self) -> None:
        sut = ServicePluginCollection([])
        assert DummyPluginOne not in sut

    def test___contains____with_unknown_plugin(self) -> None:
        sut = ServicePluginCollection([[]])
        assert DummyPluginOne not in sut

    def test___contains____with_known_plugin(self) -> None:
        sut = ServicePluginCollection([[self.PLUGIN_ONE]])
        assert DummyPluginOne in sut

    def test___contains____with_invalid_value(self) -> None:
        sut = ServicePluginCollection([])
        assert object() not in sut

    def test___getitem____without_plugins(self) -> None:
        sut = ServicePluginCollection([])
        with pytest.raises(KeyError):
            sut[DummyPluginOne]

    def test___getitem____with_unknown_plugin(self) -> None:
        sut = ServicePluginCollection([[]])
        with pytest.raises(KeyError):
            sut[DummyPluginOne]

    def test___getitem____with_known_plugin(self) -> None:
        sut = ServicePluginCollection([[DummyPluginOne()]])
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
        assert list(iter(ServicePluginCollection(plugins))) == expected

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
        assert len(ServicePluginCollection(plugins)) == expected

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
        assert list(ServicePluginCollection(plugins).keys()) == expected


class TestServicePluginDefinition:
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
            ServiceLevel(
                plugins={DummyServicePluginDefinition: [DummyServicePluginIsolated]}
            ),
            {DummyServicePluginDefinition},
            [DummyServicePluginManufacturer(DummyServicePluginIsolated)],
        ) as sut:
            assert isinstance(
                sut[key][DummyServicePluginIsolated],
                DummyServicePluginIsolated,
            )

    async def test___iter__(self) -> None:
        async with ServicePluginManager(
            ServiceLevel(
                plugins={DummyServicePluginDefinition: [DummyServicePluginIsolated]}
            ),
            {DummyServicePluginDefinition},
            [DummyServicePluginManufacturer(DummyServicePluginIsolated)],
        ) as sut:
            assert list(iter(sut)) == [DummyServicePluginDefinition]

    @pytest.mark.parametrize(
        (
            "expected",
            "plugins",
            "service_plugin_types",
            "service_plugins",
            "support_plugins",
        ),
        [
            # No service plugins.
            ({}, None, (), (), ()),
            # A single, isolated service plugin.
            (
                {
                    DummyServicePluginDefinition: [
                        DummyServicePluginIsolated.plugin().id
                    ]
                },
                {DummyServicePluginDefinition: [DummyServicePluginIsolated]},
                {DummyServicePluginDefinition},
                [DummyServicePluginManufacturer(DummyServicePluginIsolated)],
                (),
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
                {DummyServicePluginDefinition},
                [
                    DummyServicePluginManufacturer(DummyServicePluginIsolated),
                    DummyServicePluginManufacturer(DummyServicePluginRequiresIsolated),
                ],
                (),
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
                {DummyServicePluginDefinition},
                [
                    DummyServicePluginManufacturer(DummyServicePluginRequiresIsolated),
                ],
                (),
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
                {DummyServicePluginDefinition, DummyServicePluginRequirementDefinition},
                [
                    DummyServicePluginRequirementManufacturer(
                        DummyServicePluginRequirementRequiresRequiresIsolated
                    ),
                ],
                (),
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
                {DummyServicePluginOrderedDefinition},
                [
                    DummyServicePluginOrderedManufacturer(
                        DummyServicePluginOrderedAfterIsolated
                    ),
                    DummyServicePluginOrderedManufacturer(
                        DummyServicePluginOrderedIsolated
                    ),
                    DummyServicePluginOrderedManufacturer(
                        DummyServicePluginOrderedBeforeIsolated
                    ),
                ],
                (),
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
                {DummyServicePluginAutoDefinition},
                (),
                (),
            ),
            # Supported plugins.
            (
                {
                    DummyServicePluginDefinition: [
                        DummyServicePluginIsolated.plugin().id
                    ],
                },
                {
                    DummyServicePluginDefinition: [
                        DummyServicePluginIsolated,
                        DummyServicePluginRequiresIsolated,
                    ],
                },
                {DummyServicePluginDefinition},
                (),
                [DummyServicePluginRequiresIsolated],
            ),
        ],
    )
    async def test_bootstrap(
        self,
        expected: Mapping[type[ServicePluginDefinition], Iterable[MachineName]],
        plugins: Mapping[
            type[PluginDefinition], Iterable[ResolvableDiscovery[PluginDefinition]]
        ]
        | None,
        service_plugin_types: ServicePluginTypes,
        service_plugins: ServicePlugins,
        support_plugins: SupportPlugins,
        isolated_app: App,
    ) -> None:
        async with ServicePluginManager(
            ServiceLevel(plugins=plugins),
            service_plugin_types,
            service_plugins,
            support_plugins,
        ) as sut:
            assert set(sut) == set(expected)
            for plugin_type in expected:
                assert [plugin.plugin().id for plugin in sut[plugin_type]] == expected[
                    plugin_type
                ]
