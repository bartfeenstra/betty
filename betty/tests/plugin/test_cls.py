from typing import TYPE_CHECKING, Any, Self, final, override

import pytest

from betty.exception import HumanFacingException
from betty.plugin.cls import (
    ClassedPluginDefinition,
    ConfigurableIntegratable,
    NewPlugin,
    NewPluginPorter,
    NoNewPluginConfig,
    Plugin,
)
from betty.service_level import ServiceLevel
from betty.test_utils.data import DummyData
from betty.test_utils.plugin import (
    DummyPlugin,
    DummyPluginDefinition,
    DummyPluginOne,
    NewDummyPlugin,
)

if TYPE_CHECKING:
    from betty.portable import PortableData


class TestClassedPluginDefinition:
    def test__set_cls__without_plugin_class(self) -> None:
        class _Plugin:
            pass

        sut = ClassedPluginDefinition("-")
        sut(_Plugin)
        assert sut.cls is _Plugin
        assert not hasattr(_Plugin, "plugin")

    def test__set_cls__with_plugin_class(self) -> None:
        class _Plugin(Plugin):
            pass

        sut = ClassedPluginDefinition("-")
        sut(_Plugin)
        assert sut.cls is _Plugin
        assert _Plugin.plugin() is sut


@final
@DummyPluginDefinition(
    "required-data-manufacturable-dummy-plugin", config_cls=DummyData
)
class _RequiredConfigurableDummyPlugin(
    ConfigurableIntegratable[DummyData], DummyPlugin
):
    def __init__(self, *args: Any, config: DummyData, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.config = config

    @override
    @classmethod
    async def new(cls, services: ServiceLevel, config: DummyData, /) -> Self:
        return cls(config=config)


class TestNewPlugin:
    _SERVICES = ServiceLevel(
        plugins={
            DummyPluginDefinition: [
                DummyPluginOne,
                _RequiredConfigurableDummyPlugin,
            ]
        }
    )

    def test_plugin_id(self) -> None:
        sut = NewDummyPlugin(DummyPluginOne.plugin())
        assert sut.id == DummyPluginOne.plugin().id

    def test_data(self) -> None:
        NewDummyPlugin.data()

    @pytest.mark.parametrize(
        ("expected", "one", "other"),
        [
            (
                True,
                NewDummyPlugin("my-first-plugin"),
                NewDummyPlugin("my-first-plugin"),
            ),
            (
                False,
                NewDummyPlugin("my-first-plugin"),
                NewDummyPlugin("my-second-plugin"),
            ),
            (
                True,
                NewDummyPlugin("my-first-plugin", {"data": "my-first-value"}),
                NewDummyPlugin("my-first-plugin", {"data": "my-first-value"}),
            ),
            (
                False,
                NewDummyPlugin("my-first-plugin", {"data": "my-first-value"}),
                NewDummyPlugin("my-first-plugin", {"data": "my-second-value"}),
            ),
            (
                False,
                NewDummyPlugin("my-first-plugin", {"data": "my-first-value"}),
                NewDummyPlugin("my-second-plugin", {"data": "my-first-value"}),
            ),
        ],
    )
    def test___eq__(self, expected: bool, one: NewPlugin, other: NewPlugin) -> None:
        assert (one == other) is expected

    def test___eq____with_not_implemented(self) -> None:
        assert NewDummyPlugin(DummyPluginOne) != object()

    def test___hash__(self) -> None:
        new_suts = [
            lambda: NewDummyPlugin("my-first-plugin"),
            lambda: NewDummyPlugin("my-second-plugin"),
            lambda: NewDummyPlugin("my-first-plugin", DummyData()),
            lambda: NewDummyPlugin("my-second-plugin", DummyData()),
            lambda: NewDummyPlugin("my-first-plugin", {"dummy": "data"}),
            lambda: NewDummyPlugin("my-second-plugin", {"dummy": "data"}),
        ]
        for new_sut in new_suts:
            assert hash(new_sut()) == hash(new_sut())
            for other_new_sut in new_suts:
                if other_new_sut is not new_sut:
                    assert hash(new_sut()) != hash(other_new_sut())

    def test_plugin_data__with_data(self) -> None:
        configuration = DummyData()
        sut = NewDummyPlugin(_RequiredConfigurableDummyPlugin, configuration)
        assert sut.config is configuration

    def test_plugin_data__with_portable_data(self) -> None:
        configuration = DummyData.data().porter.dump(DummyData())
        sut = NewDummyPlugin(_RequiredConfigurableDummyPlugin, configuration)
        assert sut.config == sut.config
        assert sut.config == configuration

    async def test___call____without_data_manufacturable_with_data(self) -> None:
        # @todo
        raise NotImplementedError
        # with pytest.raises(PluginManufacturerError):
        #     await DummyPluginManufacturer(DummyPluginOne, DummyData())(self._SERVICES)

    async def test___call____with_required_data_manufacturable_and_data(self) -> None:
        configuration = DummyData()
        sut = NewDummyPlugin(_RequiredConfigurableDummyPlugin, configuration)
        plugin = await sut(self._SERVICES)
        assert isinstance(plugin, _RequiredConfigurableDummyPlugin)
        assert plugin.config is configuration

    async def test___call____with_required_data_manufacturable_and_portable_data(
        self,
    ) -> None:
        value = "Hello, world~"
        sut = NewDummyPlugin(_RequiredConfigurableDummyPlugin, {"value": value})
        instance = await sut(self._SERVICES)
        assert isinstance(instance, _RequiredConfigurableDummyPlugin)
        assert instance.config.value == value


class TestNewPluginPorter:
    def test_load__without_id(self) -> None:
        with pytest.raises(HumanFacingException):
            NewPluginPorter(NewDummyPlugin).load({})

    def test_load__minimal(self) -> None:
        sut = NewPluginPorter(NewDummyPlugin).load({
            "plugin": DummyPluginOne.plugin().id
        })
        assert sut.id == DummyPluginOne.plugin().id
        assert sut.config is NoNewPluginConfig

    def test_load__minimal_compact(self) -> None:
        sut = NewPluginPorter(NewDummyPlugin).load(DummyPluginOne.plugin().id)
        assert sut.id == DummyPluginOne.plugin().id
        assert sut.config is NoNewPluginConfig

    def test_load__with_configuration(self) -> None:
        configuration: PortableData = {
            "check": True,
        }
        sut = NewPluginPorter(NewDummyPlugin).load({
            "plugin": _RequiredConfigurableDummyPlugin.plugin().id,
            "data": configuration,
        })
        assert sut.id == _RequiredConfigurableDummyPlugin.plugin().id
        assert sut.config == configuration

    def test_load_keyed(self) -> None:
        sut = NewPluginPorter(NewDummyPlugin).load_keyed(DummyPluginOne.plugin().id, {})
        assert sut.id == DummyPluginOne.plugin().id
        assert sut.config is NoNewPluginConfig

    def test_load_keyed__with_configuration(self) -> None:
        configuration: PortableData = {
            "check": True,
        }
        sut = NewPluginPorter(NewDummyPlugin).load_keyed(
            _RequiredConfigurableDummyPlugin.plugin().id, {"data": configuration}
        )
        assert sut.id == _RequiredConfigurableDummyPlugin.plugin().id
        assert sut.config == configuration

    def test_dump__minimal(self) -> None:
        data = NewDummyPlugin(DummyPluginOne.plugin())
        assert NewPluginPorter(NewDummyPlugin).dump(data) == DummyPluginOne.plugin().id

    def test_dump__with_configuration(self) -> None:
        value = "Hello, world!"
        sut = NewDummyPlugin(_RequiredConfigurableDummyPlugin, DummyData(value))
        assert NewPluginPorter(NewDummyPlugin).dump(sut) == {
            "plugin": _RequiredConfigurableDummyPlugin.plugin().id,
            "data": {
                "value": value,
            },
        }

    def test_dump__with_portable_configuration(self) -> None:
        portable_configuration: PortableData = {
            "value": "Hello, world!",
        }
        data = NewDummyPlugin(_RequiredConfigurableDummyPlugin, portable_configuration)
        assert NewPluginPorter(NewDummyPlugin).dump(data) == {
            "plugin": _RequiredConfigurableDummyPlugin.plugin().id,
            "data": portable_configuration,
        }

    def test_dump_keyed__minimal(self) -> None:
        data = NewDummyPlugin(DummyPluginOne.plugin())
        assert NewPluginPorter(NewDummyPlugin).dump_keyed(data) == (
            DummyPluginOne.plugin().id,
            {},
        )

    def test_dump_keyed__with_configuration(self) -> None:
        value = "Hello, world!"
        data = NewDummyPlugin(_RequiredConfigurableDummyPlugin, DummyData(value))
        assert NewPluginPorter(NewDummyPlugin).dump_keyed(data) == (
            _RequiredConfigurableDummyPlugin.plugin().id,
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
        data = NewDummyPlugin(_RequiredConfigurableDummyPlugin, portable_configuration)
        assert NewPluginPorter(NewDummyPlugin).dump_keyed(data) == (
            _RequiredConfigurableDummyPlugin.plugin().id,
            {"data": portable_configuration},
        )
