from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, final, override

import pytest
from typing_extensions import TypeVar

from betty.data.indicator.selector import Attr
from betty.exception import HumanFacingException
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.config import (
    CountableHumanFacingPluginDefinitionConfiguration,
    HumanFacingPluginDefinitionConfiguration,
    PluginConfiguration,
    PluginDefinitionConfiguration,
    ResolvablePluginConfiguration,
    ResolvablePluginConfigurationSequence,
    new_plugins,
    resolve_plugin_configuration,
    resolve_plugin_configuration_mapping,
    resolve_plugin_configuration_sequence,
)
from betty.service.level import UNIVERSE
from betty.test_utils.data import DummyData
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)
from betty.test_utils.plugin import (
    DummyPlugin,
    DummyPluginDefinition,
    DummyPluginOne,
)
from betty.test_utils.service.level import DummyDataManufacturable
from betty.typing import Void

if TYPE_CHECKING:
    from betty.portable import PortableData

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class _DataManufacturableDummyPlugin(
    DummyDataManufacturable, Plugin["_DataManufacturableDummyPluginDefinition"]
):
    pass


@final
@PluginTypeDefinition(
    "data-manufacturable-dummy-plugin",
    label="DataManufacturable dummy plugin",
    label_plural="DataManufacturable dummy plugins",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    discovery=[lambda _: [_DataManufacturableDummyPluginOne]],
)
class _DataManufacturableDummyPluginDefinition(
    PluginDefinition[_DataManufacturableDummyPlugin]
):
    pass


@final
@_DataManufacturableDummyPluginDefinition("data-manufacturable-dummy-plugin-one")
class _DataManufacturableDummyPluginOne(_DataManufacturableDummyPlugin):
    pass


class _DummyPluginDefinitionConfiguration(PluginDefinitionConfiguration):
    @override
    def new_plugin(self) -> _PluginDefinitionT:
        raise NotImplementedError


class TestPluginDefinitionConfiguration:
    def test_id(self) -> None:
        plugin_id = "hello-world"
        sut = _DummyPluginDefinitionConfiguration(id=plugin_id)
        assert sut.id == plugin_id


class HumanFacingPluginDefinition:
    pass


class TestHumanFacingPluginDefinitionConfiguration:
    class _Sut(
        HumanFacingPluginDefinitionConfiguration, _DummyPluginDefinitionConfiguration
    ):
        @override
        def new_plugin(self) -> _PluginDefinitionT:
            raise NotImplementedError

    def test_label(self) -> None:
        label = DUMMY_LOCALIZABLE
        sut = self._Sut(id="hello-world", label=label)
        assert sut.label is label

    def test_description(self) -> None:
        description = DUMMY_LOCALIZABLE
        sut = self._Sut(
            id="hello-world", label=DUMMY_LOCALIZABLE, description=description
        )
        assert sut.description is description


class TestCountableHumanFacingPluginDefinitionConfiguration:
    class _Sut(
        CountableHumanFacingPluginDefinitionConfiguration,
        _DummyPluginDefinitionConfiguration,
    ):
        @override
        def new_plugin(self) -> _PluginDefinitionT:
            raise NotImplementedError

    def test_label_plural(self) -> None:
        label_plural = DUMMY_LOCALIZABLE
        sut = self._Sut(
            id="-dummy",
            label="-",
            label_plural=label_plural,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.label_plural is label_plural

    def test_label_countable(self) -> None:
        label_countable = DUMMY_COUNTABLE_LOCALIZABLE
        sut = self._Sut(
            id="-dummy", label="-", label_plural="-", label_countable=label_countable
        )
        assert sut.label_countable is label_countable


class TestPluginConfiguration:
    def test_id(self) -> None:
        sut = PluginConfiguration[DummyPluginDefinition, DummyPlugin](
            DummyPluginOne.plugin()
        )
        assert sut.id == DummyPluginOne.plugin().id

    @pytest.mark.parametrize(
        ("expected", "one", "other"),
        [
            (
                True,
                PluginConfiguration("my-first-plugin"),
                PluginConfiguration("my-first-plugin"),
            ),
            (
                False,
                PluginConfiguration("my-first-plugin"),
                PluginConfiguration("my-second-plugin"),
            ),
            (
                True,
                PluginConfiguration(
                    "my-first-plugin", {"configuration": "my-first-value"}
                ),
                PluginConfiguration(
                    "my-first-plugin", {"configuration": "my-first-value"}
                ),
            ),
            (
                False,
                PluginConfiguration(
                    "my-first-plugin", {"configuration": "my-first-value"}
                ),
                PluginConfiguration(
                    "my-first-plugin", {"configuration": "my-second-value"}
                ),
            ),
            (
                False,
                PluginConfiguration(
                    "my-first-plugin", {"configuration": "my-first-value"}
                ),
                PluginConfiguration(
                    "my-second-plugin", {"configuration": "my-first-value"}
                ),
            ),
        ],
    )
    def test___eq__(
        self, expected: bool, one: PluginConfiguration, other: PluginConfiguration
    ) -> None:
        assert (one == other) is expected

    def test_configuration__with_configuration(self) -> None:
        configuration = DummyData()
        sut = PluginConfiguration[
            _DataManufacturableDummyPluginDefinition, _DataManufacturableDummyPlugin
        ](_DataManufacturableDummyPluginOne.plugin(), configuration)
        assert sut.configuration is configuration

    def test_configuration__with_portable_configuration(self) -> None:
        configuration = DummyData.data().porter.dump(DummyData())
        sut = PluginConfiguration[
            _DataManufacturableDummyPluginDefinition, _DataManufacturableDummyPlugin
        ](_DataManufacturableDummyPluginOne.plugin(), configuration)
        assert sut.configuration == sut.configuration
        assert sut.configuration == configuration

    def test_load__without_id(self) -> None:
        with pytest.raises(HumanFacingException):
            PluginConfiguration.load({})

    def test_load__minimal(self) -> None:
        sut = PluginConfiguration[DummyPluginDefinition, DummyPlugin].load(
            {"id": DummyPluginOne.plugin().id}
        )
        assert sut.id == DummyPluginOne.plugin().id
        assert sut.configuration is Void()

    def test_load__minimal_compact(self) -> None:
        sut = PluginConfiguration[DummyPluginDefinition, DummyPlugin].load(
            DummyPluginOne.plugin().id
        )
        assert sut.id == DummyPluginOne.plugin().id
        assert sut.configuration is Void()

    def test_load__with_configuration(self) -> None:
        configuration: PortableData = {
            "check": True,
        }
        sut = PluginConfiguration[
            _DataManufacturableDummyPluginDefinition, _DataManufacturableDummyPlugin
        ].load(
            {
                "id": _DataManufacturableDummyPluginOne.plugin().id,
                "configuration": configuration,
            }
        )
        assert sut.id == _DataManufacturableDummyPluginOne.plugin().id
        assert sut.configuration == configuration

    def test_load_key(self) -> None:
        sut = PluginConfiguration[DummyPluginDefinition, DummyPlugin].load_key(
            {}, Attr("id"), DummyPluginOne.plugin().id
        )
        assert sut.id == DummyPluginOne.plugin().id
        assert sut.configuration is Void()

    def test_load_key__with_configuration(self) -> None:
        configuration: PortableData = {
            "check": True,
        }
        sut = PluginConfiguration[
            _DataManufacturableDummyPluginDefinition, _DataManufacturableDummyPlugin
        ].load_key(
            {"configuration": configuration},
            Attr("id"),
            _DataManufacturableDummyPluginOne.plugin().id,
        )
        assert sut.id == _DataManufacturableDummyPluginOne.plugin().id
        assert sut.configuration == configuration

    def test_dump__minimal(self) -> None:
        sut = PluginConfiguration[
            _DataManufacturableDummyPluginDefinition, DummyPlugin
        ](_DataManufacturableDummyPluginOne.plugin())
        assert sut.dump() == _DataManufacturableDummyPluginOne.plugin().id

    def test_dump__with_configuration(self) -> None:
        value = "Hello, world!"
        sut = PluginConfiguration[
            _DataManufacturableDummyPluginDefinition, _DataManufacturableDummyPlugin
        ](_DataManufacturableDummyPluginOne.plugin(), DummyData(value))
        assert sut.dump() == {
            "id": _DataManufacturableDummyPluginOne.plugin().id,
            "configuration": {
                "value": value,
            },
        }

    def test_dump__with_portable_configuration(self) -> None:
        portable_configuration = {
            "value": "Hello, world!",
        }
        sut = PluginConfiguration[
            _DataManufacturableDummyPluginDefinition, _DataManufacturableDummyPlugin
        ](_DataManufacturableDummyPluginOne.plugin(), portable_configuration)
        assert sut.dump() == {
            "id": _DataManufacturableDummyPluginOne.plugin().id,
            "configuration": portable_configuration,
        }

    def test_dump_key__minimal(self) -> None:
        sut = PluginConfiguration[
            _DataManufacturableDummyPluginDefinition, DummyPlugin
        ](_DataManufacturableDummyPluginOne.plugin())
        assert sut.dump_key(Attr("id")) == (
            _DataManufacturableDummyPluginOne.plugin().id,
            {},
        )

    def test_dump_key__with_configuration(self) -> None:
        value = "Hello, world!"
        sut = PluginConfiguration[
            _DataManufacturableDummyPluginDefinition, DummyPlugin
        ](_DataManufacturableDummyPluginOne.plugin(), DummyData(value))
        assert sut.dump_key(Attr("id")) == (
            _DataManufacturableDummyPluginOne.plugin().id,
            {
                "configuration": {
                    "value": value,
                },
            },
        )

    def test_dump_key__with_portable_configuration(self) -> None:
        portable_configuration = {
            "value": "Hello, world!",
        }
        sut = PluginConfiguration[
            _DataManufacturableDummyPluginDefinition, DummyPlugin
        ](_DataManufacturableDummyPluginOne.plugin(), portable_configuration)
        assert sut.dump_key(Attr("id")) == (
            _DataManufacturableDummyPluginOne.plugin().id,
            {"configuration": portable_configuration},
        )

    async def test_new_plugin(self) -> None:
        configuration = DummyData()
        sut = PluginConfiguration[
            _DataManufacturableDummyPluginDefinition, _DataManufacturableDummyPlugin
        ](_DataManufacturableDummyPluginOne.plugin(), configuration)
        plugin = await sut.new_plugin(
            UNIVERSE, _DataManufacturableDummyPluginDefinition
        )
        assert isinstance(plugin, _DataManufacturableDummyPluginOne)
        assert plugin.data is configuration


@pytest.mark.parametrize(
    ("expected", "value"),
    [
        (PluginConfiguration(DummyPluginOne.plugin().id), DummyPluginOne),
        (PluginConfiguration(DummyPluginOne.plugin().id), DummyPluginOne.plugin()),
        (PluginConfiguration(DummyPluginOne.plugin().id), DummyPluginOne.plugin().id),
        (
            PluginConfiguration(DummyPluginOne.plugin().id),
            PluginConfiguration(DummyPluginOne),
        ),
    ],
)
def test_resolve_plugin_configuration(
    expected: PluginConfiguration, value: ResolvablePluginConfiguration
) -> None:
    assert resolve_plugin_configuration(value) == expected


@pytest.mark.parametrize(
    ("expected", "value"),
    [
        ([PluginConfiguration(DummyPluginOne.plugin().id)], DummyPluginOne),
        ([PluginConfiguration(DummyPluginOne.plugin().id)], DummyPluginOne.plugin()),
        ([PluginConfiguration(DummyPluginOne.plugin().id)], DummyPluginOne.plugin().id),
        (
            [PluginConfiguration(DummyPluginOne.plugin().id)],
            PluginConfiguration(DummyPluginOne),
        ),
        ([PluginConfiguration(DummyPluginOne.plugin().id)], [DummyPluginOne]),
        ([PluginConfiguration(DummyPluginOne.plugin().id)], [DummyPluginOne.plugin()]),
        (
            [PluginConfiguration(DummyPluginOne.plugin().id)],
            [DummyPluginOne.plugin().id],
        ),
        (
            [PluginConfiguration(DummyPluginOne.plugin().id)],
            [PluginConfiguration(DummyPluginOne)],
        ),
    ],
)
def test_resolve_plugin_configuration_sequence(
    expected: list[PluginConfiguration], value: ResolvablePluginConfigurationSequence
) -> None:
    assert list(resolve_plugin_configuration_sequence(value)) == expected


@pytest.mark.parametrize(
    ("expected", "value"),
    [
        (
            {"key": PluginConfiguration(DummyPluginOne.plugin().id)},
            {"key": DummyPluginOne},
        ),
        (
            {"key": PluginConfiguration(DummyPluginOne.plugin().id)},
            {"key": DummyPluginOne.plugin()},
        ),
        (
            {"key": PluginConfiguration(DummyPluginOne.plugin().id)},
            {"key": DummyPluginOne.plugin().id},
        ),
        (
            {"key": PluginConfiguration(DummyPluginOne.plugin().id)},
            {"key": PluginConfiguration(DummyPluginOne)},
        ),
    ],
)
def test_resolve_plugin_configuration_mapping(
    expected: dict[Any, PluginConfiguration],
    value: Mapping[Any, ResolvablePluginConfiguration],
) -> None:
    assert dict(resolve_plugin_configuration_mapping(value)) == expected


async def test_new_plugins() -> None:
    actual = list(
        await new_plugins(
            UNIVERSE,
            DummyPluginDefinition,
            [
                DummyPluginOne,
                DummyPluginOne.plugin(),
                DummyPluginOne.plugin().id,
                PluginConfiguration(DummyPluginOne),
                PluginConfiguration(DummyPluginOne.plugin()),
                PluginConfiguration(DummyPluginOne.plugin().id),
            ],  # ty:ignore[invalid-argument-type]
        )
    )
    assert len(actual) == 6
    for plugin in actual:
        assert isinstance(plugin, DummyPluginOne)
