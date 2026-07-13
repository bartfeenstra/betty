from typing import TYPE_CHECKING, Any, Self, final, override

import pytest

from betty.exception import HumanFacingException
from betty.factory import DataManufacturable, UnsupportedTarget
from betty.plugin.factory import (
    PluginManufacturer,
    PluginManufacturerError,
    PluginManufacturerPorter,
)
from betty.service_level import ServiceLevel
from betty.test_utils.data import DummyData
from betty.test_utils.plugin import (
    DummyPlugin,
    DummyPluginDefinition,
    DummyPluginManufacturer,
    DummyPluginOne,
)
from betty.typing import Void

if TYPE_CHECKING:
    from betty.portable import PortableData


@final
@DummyPluginDefinition("required-data-manufacturable-dummy-plugin")
class _RequiredDataManufacturableDummyPlugin(
    DataManufacturable[DummyData], DummyPlugin
):
    def __init__(self, *args: Any, data: DummyData, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.data = data

    @override
    @classmethod
    def new_data_cls(cls) -> type[DummyData]:
        return DummyData

    @override
    @classmethod
    async def new(cls, services: ServiceLevel, data: DummyData, /) -> Self:
        return cls(data=data)


class TestPluginManufacturer:
    _SERVICES = ServiceLevel(
        plugins={
            DummyPluginDefinition: [
                DummyPluginOne,
                _RequiredDataManufacturableDummyPlugin,
            ]
        }
    )

    def test_plugin_id(self) -> None:
        sut = DummyPluginManufacturer(DummyPluginOne.plugin())
        assert sut.plugin_id == DummyPluginOne.plugin().id

    def test_data(self) -> None:
        DummyPluginManufacturer.data()

    @pytest.mark.parametrize(
        ("expected", "one", "other"),
        [
            (
                True,
                DummyPluginManufacturer("my-first-plugin"),
                DummyPluginManufacturer("my-first-plugin"),
            ),
            (
                False,
                DummyPluginManufacturer("my-first-plugin"),
                DummyPluginManufacturer("my-second-plugin"),
            ),
            (
                True,
                DummyPluginManufacturer(
                    "my-first-plugin",
                    {"data": "my-first-value"},  # ty:ignore[invalid-argument-type]
                ),
                DummyPluginManufacturer(
                    "my-first-plugin",
                    {"data": "my-first-value"},  # ty:ignore[invalid-argument-type]
                ),
            ),
            (
                False,
                DummyPluginManufacturer(
                    "my-first-plugin",
                    {"data": "my-first-value"},  # ty:ignore[invalid-argument-type]
                ),
                DummyPluginManufacturer(
                    "my-first-plugin",
                    {"data": "my-second-value"},  # ty:ignore[invalid-argument-type]
                ),
            ),
            (
                False,
                DummyPluginManufacturer(
                    "my-first-plugin",
                    {"data": "my-first-value"},  # ty:ignore[invalid-argument-type]
                ),
                DummyPluginManufacturer(
                    "my-second-plugin",
                    {"data": "my-first-value"},  # ty:ignore[invalid-argument-type]
                ),
            ),
        ],
    )
    def test___eq__(
        self, expected: bool, one: PluginManufacturer, other: PluginManufacturer
    ) -> None:
        assert (one == other) is expected

    def test___eq____with_not_implemented(self) -> None:
        assert DummyPluginManufacturer(DummyPluginOne) != object()

    def test___hash__(self) -> None:
        new_suts = [
            lambda: DummyPluginManufacturer("my-first-plugin"),
            lambda: DummyPluginManufacturer("my-second-plugin"),
            lambda: DummyPluginManufacturer("my-first-plugin", DummyData()),
            lambda: DummyPluginManufacturer("my-second-plugin", DummyData()),
            lambda: DummyPluginManufacturer(
                "my-first-plugin",
                {"dummy": "data"},  # ty:ignore[invalid-argument-type]
            ),
            lambda: DummyPluginManufacturer(
                "my-second-plugin",
                {"dummy": "data"},  # ty:ignore[invalid-argument-type]
            ),
        ]
        for new_sut in new_suts:
            assert hash(new_sut()) == hash(new_sut())
            for other_new_sut in new_suts:
                if other_new_sut is not new_sut:
                    assert hash(new_sut()) != hash(other_new_sut())

    def test_plugin_data__with_data(self) -> None:
        configuration = DummyData()
        sut = DummyPluginManufacturer(
            _RequiredDataManufacturableDummyPlugin, configuration
        )
        assert sut.plugin_data is configuration

    def test_plugin_data__with_portable_data(self) -> None:
        configuration = DummyData.data().porter.dump(DummyData())
        sut = DummyPluginManufacturer(
            _RequiredDataManufacturableDummyPlugin, configuration
        )
        assert sut.plugin_data == sut.plugin_data
        assert sut.plugin_data == configuration

    async def test___call____with_required_data_manufacturable_without_data(
        self,
    ) -> None:
        DummyPluginManufacturer(_RequiredDataManufacturableDummyPlugin)
        with pytest.raises(UnsupportedTarget):
            await DummyPluginManufacturer(_RequiredDataManufacturableDummyPlugin)(
                self._SERVICES
            )

    async def test___call____without_data_manufacturable_with_data(self) -> None:
        with pytest.raises(PluginManufacturerError):
            await DummyPluginManufacturer(DummyPluginOne, DummyData())(self._SERVICES)

    async def test___call____with_required_data_manufacturable_and_data(self) -> None:
        configuration = DummyData()
        sut = DummyPluginManufacturer(
            _RequiredDataManufacturableDummyPlugin, configuration
        )
        plugin = await sut(self._SERVICES)
        assert isinstance(plugin, _RequiredDataManufacturableDummyPlugin)
        assert plugin.data is configuration

    async def test___call____with_required_data_manufacturable_and_portable_data(
        self,
    ) -> None:
        value = "Hello, world~"
        sut = DummyPluginManufacturer(
            _RequiredDataManufacturableDummyPlugin,
            {"value": value},  # ty:ignore[invalid-argument-type]
        )
        instance = await sut(self._SERVICES)
        assert isinstance(instance, _RequiredDataManufacturableDummyPlugin)
        assert instance.data.value == value


class TestPluginManufacturerPorter:
    def test_load__without_id(self) -> None:
        with pytest.raises(HumanFacingException):
            PluginManufacturerPorter(DummyPluginManufacturer).load({})

    def test_load__minimal(self) -> None:
        sut = PluginManufacturerPorter(DummyPluginManufacturer).load({
            "plugin": DummyPluginOne.plugin().id
        })
        assert sut.plugin_id == DummyPluginOne.plugin().id
        assert sut.plugin_data is Void

    def test_load__minimal_compact(self) -> None:
        sut = PluginManufacturerPorter(DummyPluginManufacturer).load(
            DummyPluginOne.plugin().id
        )
        assert sut.plugin_id == DummyPluginOne.plugin().id
        assert sut.plugin_data is Void

    def test_load__with_configuration(self) -> None:
        configuration: PortableData = {
            "check": True,
        }
        sut = PluginManufacturerPorter(DummyPluginManufacturer).load({
            "plugin": _RequiredDataManufacturableDummyPlugin.plugin().id,
            "data": configuration,
        })
        assert sut.plugin_id == _RequiredDataManufacturableDummyPlugin.plugin().id
        assert sut.plugin_data == configuration

    def test_load_keyed(self) -> None:
        sut = PluginManufacturerPorter(DummyPluginManufacturer).load_keyed(
            DummyPluginOne.plugin().id, {}
        )
        assert sut.plugin_id == DummyPluginOne.plugin().id
        assert sut.plugin_data is Void

    def test_load_keyed__with_configuration(self) -> None:
        configuration: PortableData = {
            "check": True,
        }
        sut = PluginManufacturerPorter(DummyPluginManufacturer).load_keyed(
            _RequiredDataManufacturableDummyPlugin.plugin().id, {"data": configuration}
        )
        assert sut.plugin_id == _RequiredDataManufacturableDummyPlugin.plugin().id
        assert sut.plugin_data == configuration

    def test_dump__minimal(self) -> None:
        data = DummyPluginManufacturer(DummyPluginOne.plugin())
        assert (
            PluginManufacturerPorter(DummyPluginManufacturer).dump(data)
            == DummyPluginOne.plugin().id
        )

    def test_dump__with_configuration(self) -> None:
        value = "Hello, world!"
        sut = DummyPluginManufacturer(
            _RequiredDataManufacturableDummyPlugin, DummyData(value)
        )
        assert PluginManufacturerPorter(DummyPluginManufacturer).dump(sut) == {
            "plugin": _RequiredDataManufacturableDummyPlugin.plugin().id,
            "data": {
                "value": value,
            },
        }

    def test_dump__with_portable_configuration(self) -> None:
        portable_configuration: PortableData = {
            "value": "Hello, world!",
        }
        data = DummyPluginManufacturer(
            _RequiredDataManufacturableDummyPlugin, portable_configuration
        )
        assert PluginManufacturerPorter(DummyPluginManufacturer).dump(data) == {
            "plugin": _RequiredDataManufacturableDummyPlugin.plugin().id,
            "data": portable_configuration,
        }

    def test_dump_keyed__minimal(self) -> None:
        data = DummyPluginManufacturer(DummyPluginOne.plugin())
        assert PluginManufacturerPorter(DummyPluginManufacturer).dump_keyed(data) == (
            DummyPluginOne.plugin().id,
            {},
        )

    def test_dump_keyed__with_configuration(self) -> None:
        value = "Hello, world!"
        data = DummyPluginManufacturer(
            _RequiredDataManufacturableDummyPlugin, DummyData(value)
        )
        assert PluginManufacturerPorter(DummyPluginManufacturer).dump_keyed(data) == (
            _RequiredDataManufacturableDummyPlugin.plugin().id,
            {
                "data": {
                    "value": value,
                },
            },
        )

    def test_dump_keyed__with_portable_configuration(self) -> None:
        portable_configuration: PortableData = {
            "value": "Hello, world!",
        }
        data = DummyPluginManufacturer(
            _RequiredDataManufacturableDummyPlugin, portable_configuration
        )
        assert PluginManufacturerPorter(DummyPluginManufacturer).dump_keyed(data) == (
            _RequiredDataManufacturableDummyPlugin.plugin().id,
            {"data": portable_configuration},
        )
