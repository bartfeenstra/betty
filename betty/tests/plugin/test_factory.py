from typing import TYPE_CHECKING, Any, Self, final, override

import pytest

from betty.exception import HumanFacingException
from betty.factory import DataManufacturable, UnsupportedTarget
from betty.indicator.selector import Attr
from betty.plugin.factory import PluginManufacturer, PluginManufacturerError
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
                DummyPluginManufacturer("my-first-plugin", {"data": "my-first-value"}),
                DummyPluginManufacturer("my-first-plugin", {"data": "my-first-value"}),
            ),
            (
                False,
                DummyPluginManufacturer("my-first-plugin", {"data": "my-first-value"}),
                DummyPluginManufacturer("my-first-plugin", {"data": "my-second-value"}),
            ),
            (
                False,
                DummyPluginManufacturer("my-first-plugin", {"data": "my-first-value"}),
                DummyPluginManufacturer("my-second-plugin", {"data": "my-first-value"}),
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
            lambda: DummyPluginManufacturer("my-first-plugin", {"dummy": "data"}),
            lambda: DummyPluginManufacturer("my-second-plugin", {"dummy": "data"}),
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

    def test_load__without_id(self) -> None:
        with pytest.raises(HumanFacingException):
            PluginManufacturer.load({})

    def test_load__minimal(self) -> None:
        sut = DummyPluginManufacturer.load({"plugin": DummyPluginOne.plugin().id})
        assert sut.plugin_id == DummyPluginOne.plugin().id
        assert sut.plugin_data is Void

    def test_load__minimal_compact(self) -> None:
        sut = DummyPluginManufacturer.load(DummyPluginOne.plugin().id)
        assert sut.plugin_id == DummyPluginOne.plugin().id
        assert sut.plugin_data is Void

    def test_load__with_configuration(self) -> None:
        configuration: PortableData = {
            "check": True,
        }  # ty:ignore[invalid-assignment]
        sut = DummyPluginManufacturer.load({
            "plugin": _RequiredDataManufacturableDummyPlugin.plugin().id,
            "data": configuration,
        })
        assert sut.plugin_id == _RequiredDataManufacturableDummyPlugin.plugin().id
        assert sut.plugin_data == configuration

    def test_load_key(self) -> None:
        sut = DummyPluginManufacturer.load_key(
            {}, Attr("plugin"), DummyPluginOne.plugin().id
        )
        assert sut.plugin_id == DummyPluginOne.plugin().id
        assert sut.plugin_data is Void

    def test_load_key__with_configuration(self) -> None:
        configuration: PortableData = {
            "check": True,
        }  # ty:ignore[invalid-assignment]
        sut = DummyPluginManufacturer.load_key(
            {"data": configuration},
            Attr("plugin"),
            _RequiredDataManufacturableDummyPlugin.plugin().id,
        )
        assert sut.plugin_id == _RequiredDataManufacturableDummyPlugin.plugin().id
        assert sut.plugin_data == configuration

    def test_dump__minimal(self) -> None:
        sut = DummyPluginManufacturer(DummyPluginOne.plugin())
        assert sut.dump() == DummyPluginOne.plugin().id

    def test_dump__with_configuration(self) -> None:
        value = "Hello, world!"
        sut = DummyPluginManufacturer(
            _RequiredDataManufacturableDummyPlugin, DummyData(value)
        )
        assert sut.dump() == {
            "plugin": _RequiredDataManufacturableDummyPlugin.plugin().id,
            "data": {
                "value": value,
            },
        }

    def test_dump__with_portable_configuration(self) -> None:
        portable_configuration = {
            "value": "Hello, world!",
        }
        sut = DummyPluginManufacturer(
            _RequiredDataManufacturableDummyPlugin, portable_configuration
        )
        assert sut.dump() == {
            "plugin": _RequiredDataManufacturableDummyPlugin.plugin().id,
            "data": portable_configuration,
        }

    def test_dump_key__minimal(self) -> None:
        sut = DummyPluginManufacturer(DummyPluginOne.plugin())
        assert sut.dump_key(Attr("plugin")) == (
            DummyPluginOne.plugin().id,
            {},
        )

    def test_dump_key__with_configuration(self) -> None:
        value = "Hello, world!"
        sut = DummyPluginManufacturer(
            _RequiredDataManufacturableDummyPlugin, DummyData(value)
        )
        assert sut.dump_key(Attr("plugin")) == (
            _RequiredDataManufacturableDummyPlugin.plugin().id,
            {
                "data": {
                    "value": value,
                },
            },
        )

    def test_dump_key__with_portable_configuration(self) -> None:
        portable_configuration = {
            "value": "Hello, world!",
        }
        sut = DummyPluginManufacturer(
            _RequiredDataManufacturableDummyPlugin, portable_configuration
        )
        assert sut.dump_key(Attr("plugin")) == (
            _RequiredDataManufacturableDummyPlugin.plugin().id,
            {"data": portable_configuration},
        )

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
            _RequiredDataManufacturableDummyPlugin, {"value": value}
        )
        instance = await sut(self._SERVICES)
        assert isinstance(instance, _RequiredDataManufacturableDummyPlugin)
        assert instance.data.value == value
