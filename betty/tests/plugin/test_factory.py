import builtins
from typing import TYPE_CHECKING, final, override

import pytest

from betty.data.indicator.selector import Attr
from betty.exception import HumanFacingException
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.factory import PluginManufacturer
from betty.service.level import ServiceLevel
from betty.test_utils.data import DummyData
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
)
from betty.test_utils.plugin import (
    DummyPluginManufacturer,
    DummyPluginOne,
)
from betty.test_utils.service.level import DummyDataManufacturable
from betty.typing import Void

if TYPE_CHECKING:
    from betty.portable import PortableData


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


class _DataManufacturableDummyPluginManufacturer(
    PluginManufacturer[
        _DataManufacturableDummyPluginDefinition, _DataManufacturableDummyPlugin
    ]
):
    @override
    @classmethod
    def type(cls) -> builtins.type[_DataManufacturableDummyPluginDefinition]:
        return _DataManufacturableDummyPluginDefinition


@final
@_DataManufacturableDummyPluginDefinition("data-manufacturable-dummy-plugin-one")
class _DataManufacturableDummyPluginOne(_DataManufacturableDummyPlugin):
    pass


class TestPluginManufacturer:
    def test_plugin_id(self) -> None:
        sut = DummyPluginManufacturer(DummyPluginOne.plugin())
        assert sut.plugin_id == DummyPluginOne.plugin().id

    @pytest.mark.parametrize(
        ("expected", "one", "other"),
        [
            (
                True,
                _DataManufacturableDummyPluginManufacturer("my-first-plugin"),
                _DataManufacturableDummyPluginManufacturer("my-first-plugin"),
            ),
            (
                False,
                _DataManufacturableDummyPluginManufacturer("my-first-plugin"),
                _DataManufacturableDummyPluginManufacturer("my-second-plugin"),
            ),
            (
                True,
                _DataManufacturableDummyPluginManufacturer(
                    "my-first-plugin", {"data": "my-first-value"}
                ),
                _DataManufacturableDummyPluginManufacturer(
                    "my-first-plugin", {"data": "my-first-value"}
                ),
            ),
            (
                False,
                _DataManufacturableDummyPluginManufacturer(
                    "my-first-plugin", {"data": "my-first-value"}
                ),
                _DataManufacturableDummyPluginManufacturer(
                    "my-first-plugin", {"data": "my-second-value"}
                ),
            ),
            (
                False,
                _DataManufacturableDummyPluginManufacturer(
                    "my-first-plugin", {"data": "my-first-value"}
                ),
                _DataManufacturableDummyPluginManufacturer(
                    "my-second-plugin", {"data": "my-first-value"}
                ),
            ),
        ],
    )
    def test___eq__(
        self, expected: bool, one: PluginManufacturer, other: PluginManufacturer
    ) -> None:
        assert (one == other) is expected

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
        sut = _DataManufacturableDummyPluginManufacturer(
            _DataManufacturableDummyPluginOne, configuration
        )
        assert sut.plugin_data is configuration

    def test_plugin_data__with_portable_data(self) -> None:
        configuration = DummyData.data().porter.dump(DummyData())
        sut = _DataManufacturableDummyPluginManufacturer(
            _DataManufacturableDummyPluginOne, configuration
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
        }
        sut = _DataManufacturableDummyPluginManufacturer.load(
            {
                "plugin": _DataManufacturableDummyPluginOne.plugin().id,
                "data": configuration,
            }
        )
        assert sut.plugin_id == _DataManufacturableDummyPluginOne.plugin().id
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
        }
        sut = _DataManufacturableDummyPluginManufacturer.load_key(
            {"data": configuration},
            Attr("plugin"),
            _DataManufacturableDummyPluginOne.plugin().id,
        )
        assert sut.plugin_id == _DataManufacturableDummyPluginOne.plugin().id
        assert sut.plugin_data == configuration

    def test_dump__minimal(self) -> None:
        sut = DummyPluginManufacturer(DummyPluginOne.plugin())
        assert sut.dump() == DummyPluginOne.plugin().id

    def test_dump__with_configuration(self) -> None:
        value = "Hello, world!"
        sut = _DataManufacturableDummyPluginManufacturer(
            _DataManufacturableDummyPluginOne, DummyData(value)
        )
        assert sut.dump() == {
            "plugin": _DataManufacturableDummyPluginOne.plugin().id,
            "data": {
                "value": value,
            },
        }

    def test_dump__with_portable_configuration(self) -> None:
        portable_configuration = {
            "value": "Hello, world!",
        }
        sut = _DataManufacturableDummyPluginManufacturer(
            _DataManufacturableDummyPluginOne, portable_configuration
        )
        assert sut.dump() == {
            "plugin": _DataManufacturableDummyPluginOne.plugin().id,
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
        sut = _DataManufacturableDummyPluginManufacturer(
            _DataManufacturableDummyPluginOne, DummyData(value)
        )
        assert sut.dump_key(Attr("plugin")) == (
            _DataManufacturableDummyPluginOne.plugin().id,
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
        sut = _DataManufacturableDummyPluginManufacturer(
            _DataManufacturableDummyPluginOne, portable_configuration
        )
        assert sut.dump_key(Attr("plugin")) == (
            _DataManufacturableDummyPluginOne.plugin().id,
            {"data": portable_configuration},
        )

    async def test___call__(self) -> None:
        configuration = DummyData()
        sut = _DataManufacturableDummyPluginManufacturer(
            _DataManufacturableDummyPluginOne, configuration
        )
        plugin = await sut(
            ServiceLevel(
                plugins={
                    _DataManufacturableDummyPluginDefinition: [
                        _DataManufacturableDummyPluginOne
                    ]
                }
            )
        )
        assert isinstance(plugin, _DataManufacturableDummyPluginOne)
        assert plugin.data is configuration
