from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.data.indicator.selector import Attr
from betty.exception import HumanFacingException
from betty.plugin.config import (
    CountableHumanFacingPluginDefinitionConfiguration,
    HumanFacingPluginDefinitionConfiguration,
    PluginConfiguration,
    PluginDefinitionConfiguration,
    ResolvablePluginConfiguration,
    ResolvablePluginConfigurations,
    _PluginDefinitionT,
    resolve_plugin_configuration,
    resolve_plugin_configurations,
)
from betty.test_utils.config import ConfigurationTestBase
from betty.test_utils.data import DummyData
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)
from betty.test_utils.plugin import DummyPlugin, DummyPluginDefinition, DummyPluginOne
from betty.test_utils.plugin.config import (
    ConfigurableDummyPlugin,
    ConfigurableDummyPluginDefinition,
    ConfigurableDummyPluginOne,
)
from betty.typing import Void

if TYPE_CHECKING:
    from betty.portable import PortableData


class _DummyPluginDefinitionConfiguration(PluginDefinitionConfiguration):
    @override
    def new_plugin(self) -> _PluginDefinitionT:
        raise NotImplementedError


class TestPluginDefinitionConfiguration:
    async def test_id(self) -> None:
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

    async def test_label(self) -> None:
        label = DUMMY_LOCALIZABLE
        sut = self._Sut(id="hello-world", label=label)
        assert sut.label is label

    async def test_description(self) -> None:
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

    async def test_label_plural(self) -> None:
        label_plural = DUMMY_LOCALIZABLE
        sut = self._Sut(
            id="-",
            label="-",
            label_plural=label_plural,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.label_plural is label_plural

    async def test_label_countable(self) -> None:
        label_countable = DUMMY_COUNTABLE_LOCALIZABLE
        sut = self._Sut(
            id="-", label="-", label_plural="-", label_countable=label_countable
        )
        assert sut.label_countable is label_countable


class TestPluginConfiguration(ConfigurationTestBase[PluginConfiguration]):
    sut_cls = PluginConfiguration

    def test_id(self) -> None:
        sut = PluginConfiguration[DummyPluginDefinition, DummyPlugin](
            DummyPluginOne.plugin()
        )
        assert sut.id == DummyPluginOne.plugin().id

    def test_configuration__with_configuration(self) -> None:
        configuration = DummyData()
        sut = PluginConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin(), configuration)
        assert sut.configuration is configuration

    def test_configuration__with_portable_configuration(self) -> None:
        configuration = DummyData.data().porter.dump(DummyData())
        sut = PluginConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin(), configuration)
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
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ].load(
            {
                "id": ConfigurableDummyPluginOne.plugin().id,
                "configuration": configuration,
            }
        )
        assert sut.id == ConfigurableDummyPluginOne.plugin().id
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
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ].load_key(
            {"configuration": configuration},
            Attr("id"),
            ConfigurableDummyPluginOne.plugin().id,
        )
        assert sut.id == ConfigurableDummyPluginOne.plugin().id
        assert sut.configuration == configuration

    def test_dump__minimal(self) -> None:
        sut = PluginConfiguration[ConfigurableDummyPluginDefinition, DummyPlugin](
            ConfigurableDummyPluginOne.plugin()
        )
        assert sut.dump() == ConfigurableDummyPluginOne.plugin().id

    def test_dump__with_configuration(self) -> None:
        value = "Hello, world!"
        sut = PluginConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin(), DummyData(value))
        assert sut.dump() == {
            "id": ConfigurableDummyPluginOne.plugin().id,
            "configuration": {
                "value": value,
            },
        }

    def test_dump__with_portable_configuration(self) -> None:
        portable_configuration = {
            "value": "Hello, world!",
        }
        sut = PluginConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin(), portable_configuration)
        assert sut.dump() == {
            "id": ConfigurableDummyPluginOne.plugin().id,
            "configuration": portable_configuration,
        }

    def test_dump_key__minimal(self) -> None:
        sut = PluginConfiguration[ConfigurableDummyPluginDefinition, DummyPlugin](
            ConfigurableDummyPluginOne.plugin()
        )
        assert sut.dump_key(Attr("id")) == (ConfigurableDummyPluginOne.plugin().id, {})

    def test_dump_key__with_configuration(self) -> None:
        value = "Hello, world!"
        sut = PluginConfiguration[ConfigurableDummyPluginDefinition, DummyPlugin](
            ConfigurableDummyPluginOne.plugin(), DummyData(value)
        )
        assert sut.dump_key(Attr("id")) == (
            ConfigurableDummyPluginOne.plugin().id,
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
        sut = PluginConfiguration[ConfigurableDummyPluginDefinition, DummyPlugin](
            ConfigurableDummyPluginOne.plugin(), portable_configuration
        )
        assert sut.dump_key(Attr("id")) == (
            ConfigurableDummyPluginOne.plugin().id,
            {"configuration": portable_configuration},
        )


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
def test_resolve_plugin_configurations(
    expected: list[PluginConfiguration], value: ResolvablePluginConfigurations
) -> None:
    assert list(resolve_plugin_configurations(value)) == expected
