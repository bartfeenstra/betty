from collections.abc import Iterable
from typing import TypeVar, Mapping, cast

import pytest
from typing_extensions import override

from betty.assertion.error import AssertionFailed
from betty.config import DefaultConfigurable
from betty.config.collections import ConfigurationCollection
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import ShorthandStaticTranslations
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import MachineName
from betty.plugin import Plugin
from betty.plugin.config import (
    PluginConfiguration,
    PluginConfigurationPluginConfigurationMapping,
    PluginInstanceConfiguration,
    PluginInstanceConfigurationMapping,
    PluginIdentifierKeyConfigurationMapping,
)
from betty.plugin.static import StaticPluginRepository
from betty.serde.dump import Dump
from betty.test_utils.assertion.error import raises_error
from betty.test_utils.config import DummyConfiguration
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase
from betty.test_utils.plugin import DummyPlugin

_PluginT = TypeVar("_PluginT", bound=Plugin)


class _DummyDefaultConfigurablePlugin(
    DefaultConfigurable[DummyConfiguration], DummyPlugin
):
    def __init__(self):
        super().__init__(configuration=self.new_default_configuration())

    @override
    @classmethod
    def new_default_configuration(
        cls,
    ) -> DummyConfiguration:
        return DummyConfiguration()


class TestPluginConfiguration:
    async def test_load(self) -> None:
        plugin_id = "hello-world"
        dump: Dump = {
            "id": plugin_id,
            "label": "",
        }
        sut = PluginConfiguration("-", "")
        sut.load(dump)
        assert sut.id == plugin_id

    async def test_load_with_undetermined_label(self) -> None:
        label = "Hello, world!"
        dump: Dump = {
            "id": "hello-world",
            "label": label,
        }
        sut = PluginConfiguration("-", "")
        sut.load(dump)
        assert sut.label[UNDETERMINED_LOCALE] == label

    async def test_load_with_expanded_label(self) -> None:
        label = "Hello, world!"
        dump: Dump = {
            "id": "hello-world",
            "label": {
                DEFAULT_LOCALIZER.locale: label,
            },
        }
        sut = PluginConfiguration("-", "")
        sut.load(dump)
        assert sut.label[DEFAULT_LOCALIZER.locale] == label

    async def test_load_with_undetermined_description(self) -> None:
        description = "Hello, world!"
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "description": description,
        }
        sut = PluginConfiguration("-", "")
        sut.load(dump)
        assert sut.description[UNDETERMINED_LOCALE] == description

    async def test_load_with_expanded_description(self) -> None:
        description = "Hello, world!"
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "description": {
                DEFAULT_LOCALIZER.locale: description,
            },
        }
        sut = PluginConfiguration("-", "")
        sut.load(dump)
        assert sut.description[DEFAULT_LOCALIZER.locale] == description

    async def test_dump(self) -> None:
        plugin_id = "hello-world"
        sut = PluginConfiguration(plugin_id, "")
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["id"] == plugin_id

    async def test_dump_with_undetermined_label(self) -> None:
        label = "Hello, world!"
        sut = PluginConfiguration("hello-world", label)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["label"] == label

    async def test_dump_with_expanded_label(self) -> None:
        label = "Hello, world!"
        sut = PluginConfiguration("hello-world", {DEFAULT_LOCALIZER.locale: label})
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["label"] == {
            DEFAULT_LOCALIZER.locale: label,
        }

    async def test_dump_with_undetermined_description(self) -> None:
        description = "Hello, world!"
        sut = PluginConfiguration("hello-world", "", description=description)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["description"] == description

    async def test_dump_with_expanded_description(self) -> None:
        description = "Hello, world!"
        sut = PluginConfiguration(
            "hello-world",
            "",
            description={DEFAULT_LOCALIZER.locale: description},
        )
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["description"] == {
            DEFAULT_LOCALIZER.locale: description,
        }

    async def test_id(self) -> None:
        plugin_id = "hello-world"
        sut = PluginConfiguration(plugin_id, "")
        assert sut.id == plugin_id

    @pytest.mark.parametrize(
        ("expected_locale", "expected_label", "init_label"),
        [
            ("und", "Hello, world!", "Hello, world!"),
            (
                DEFAULT_LOCALIZER.locale,
                "Hello, world!",
                {DEFAULT_LOCALIZER.locale: "Hello, world!"},
            ),
        ],
    )
    async def test_label(
        self,
        expected_locale: str,
        expected_label: str,
        init_label: ShorthandStaticTranslations,
    ) -> None:
        plugin_id = "hello-world"
        sut = PluginConfiguration(plugin_id, init_label)
        assert sut.label[expected_locale] == expected_label

    @pytest.mark.parametrize(
        ("expected_locale", "expected_description", "init_description"),
        [
            ("und", "Hello, world!", "Hello, world!"),
            (
                DEFAULT_LOCALIZER.locale,
                "Hello, world!",
                {DEFAULT_LOCALIZER.locale: "Hello, world!"},
            ),
        ],
    )
    async def test_description(
        self,
        expected_locale: str,
        expected_description: str,
        init_description: ShorthandStaticTranslations,
    ) -> None:
        plugin_id = "hello-world"
        sut = PluginConfiguration(plugin_id, "", description=init_description)
        assert sut.description[expected_locale] == expected_description


class TestPluginConfigurationPluginConfigurationMapping(
    ConfigurationMappingTestBase[MachineName, PluginConfiguration]
):
    async def get_sut(
        self, configurations: Iterable[PluginConfiguration] | None = None
    ) -> ConfigurationCollection[MachineName, PluginConfiguration]:
        return PluginConfigurationPluginConfigurationMapping(configurations)

    def get_configuration_keys(
        self,
    ) -> tuple[MachineName, MachineName, MachineName, MachineName]:
        return (
            "hello-world-1",
            "hello-world-2",
            "hello-world-3",
            "hello-world-4",
        )

    async def get_configurations(
        self,
    ) -> tuple[
        PluginConfiguration,
        PluginConfiguration,
        PluginConfiguration,
        PluginConfiguration,
    ]:
        return (
            PluginConfiguration(self.get_configuration_keys()[0], ""),
            PluginConfiguration(self.get_configuration_keys()[1], ""),
            PluginConfiguration(self.get_configuration_keys()[2], ""),
            PluginConfiguration(self.get_configuration_keys()[3], ""),
        )


class TestPluginInstanceConfiguration:
    def test___init___with_configuration(self):
        plugin = DummyPlugin
        value = "Hello, world!"
        sut = PluginInstanceConfiguration(
            plugin,
            configuration=DummyConfiguration(value),
        )
        assert sut.configuration == {"value": value}

    def test___init___with_configuration_dump(self):
        plugin = DummyPlugin
        configuration: Dump = {
            "value": "Hello, world!",
        }
        sut = PluginInstanceConfiguration(
            plugin,
            configuration=configuration,
        )
        assert sut.configuration == configuration

    def test_id(self) -> None:
        plugin = DummyPlugin
        sut = PluginInstanceConfiguration(plugin)
        assert sut.id == plugin.plugin_id()

    def test_configuration(self) -> None:
        plugin = _DummyDefaultConfigurablePlugin
        configuration = DummyConfiguration()
        sut = PluginInstanceConfiguration(plugin, configuration=configuration)
        assert sut.configuration == configuration.dump()

    def test_load_without_id(self) -> None:
        plugin = DummyPlugin
        with raises_error(error_type=AssertionFailed):
            (PluginInstanceConfiguration(plugin)).load({})

    def test_load_minimal(self) -> None:
        plugin = DummyPlugin
        sut = PluginInstanceConfiguration(plugin)
        sut.load({"id": plugin.plugin_id()})
        assert sut.id == plugin.plugin_id()

    def test_load_with_configuration(self) -> None:
        plugin = _DummyDefaultConfigurablePlugin
        sut = PluginInstanceConfiguration(plugin)
        configuration: Dump = {
            "check": True,
        }
        sut.load(
            {
                "id": plugin.plugin_id(),
                "configuration": configuration,
            }
        )
        assert sut.configuration == configuration

    def test_dump_should_dump_minimal(self) -> None:
        plugin = DummyPlugin
        sut = PluginInstanceConfiguration(plugin)
        assert sut.dump() == plugin.plugin_id()

    def test_dump_should_dump_configuration(self) -> None:
        plugin = _DummyDefaultConfigurablePlugin
        value = "Hello, world!"
        sut = PluginInstanceConfiguration(
            plugin, configuration=DummyConfiguration(value)
        )
        expected = {
            "id": plugin.plugin_id(),
            "configuration": {
                "value": value,
            },
        }
        assert sut.dump() == expected

    async def test_new_plugin_instance_with_configurable_plugin_with_configuration(
        self,
    ) -> None:
        plugin = _DummyDefaultConfigurablePlugin
        value = "Hello, world!"
        sut = PluginInstanceConfiguration(
            plugin, configuration=DummyConfiguration(value)
        )
        repository = StaticPluginRepository(plugin)
        instance = await sut.new_plugin_instance(repository)
        assert isinstance(instance, plugin)
        assert instance.configuration.value == value

    async def test_new_plugin_instance_with_configurable_plugin_without_configuration(
        self,
    ) -> None:
        plugin = _DummyDefaultConfigurablePlugin
        sut = PluginInstanceConfiguration(plugin)
        repository = StaticPluginRepository(plugin)
        instance = await sut.new_plugin_instance(repository)
        assert isinstance(instance, plugin)

    async def test_new_plugin_instance_with_non_configurable_plugin_with_configuration(
        self,
    ) -> None:
        plugin = DummyPlugin
        value = "Hello, world!"
        sut = PluginInstanceConfiguration(
            plugin, configuration=DummyConfiguration(value)
        )
        repository = StaticPluginRepository(plugin)
        with pytest.raises(AssertionFailed):
            await sut.new_plugin_instance(repository)

    async def test_new_plugin_instance_with_non_configurable_plugin_without_configuration(
        self,
    ) -> None:
        plugin = DummyPlugin
        sut = PluginInstanceConfiguration(plugin)
        repository = StaticPluginRepository(plugin)
        instance = await sut.new_plugin_instance(repository)
        assert isinstance(instance, plugin)


class PluginInstanceConfigurationMappingTestDummyPlugin0(DummyPlugin):
    pass


class PluginInstanceConfigurationMappingTestDummyPlugin1(DummyPlugin):
    pass


class PluginInstanceConfigurationMappingTestDummyPlugin2(DummyPlugin):
    pass


class PluginInstanceConfigurationMappingTestDummyPlugin3(DummyPlugin):
    pass


class TestPluginInstanceConfigurationMapping(
    ConfigurationMappingTestBase[MachineName, PluginInstanceConfiguration]
):
    @override
    def get_configuration_keys(
        self,
    ) -> tuple[MachineName, MachineName, MachineName, MachineName]:
        return (
            PluginInstanceConfigurationMappingTestDummyPlugin0.plugin_id(),
            PluginInstanceConfigurationMappingTestDummyPlugin1.plugin_id(),
            PluginInstanceConfigurationMappingTestDummyPlugin2.plugin_id(),
            PluginInstanceConfigurationMappingTestDummyPlugin3.plugin_id(),
        )

    @override
    async def get_sut(
        self,
        configurations: Iterable[PluginInstanceConfiguration] | None = None,
    ) -> PluginInstanceConfigurationMapping[DummyPlugin]:
        return PluginInstanceConfigurationMapping(configurations)

    @override
    async def get_configurations(
        self,
    ) -> tuple[
        PluginInstanceConfiguration,
        PluginInstanceConfiguration,
        PluginInstanceConfiguration,
        PluginInstanceConfiguration,
    ]:
        return (
            PluginInstanceConfiguration(self.get_configuration_keys()[0]),
            PluginInstanceConfiguration(self.get_configuration_keys()[1]),
            PluginInstanceConfiguration(self.get_configuration_keys()[2]),
            PluginInstanceConfiguration(self.get_configuration_keys()[3]),
        )


class _DummyPluginIdentifierKeyConfigurationMapping(
    PluginIdentifierKeyConfigurationMapping[DummyPlugin, DummyConfiguration]
):
    @override
    def _dump_key(self, item_dump: Dump) -> tuple[Dump, str]:
        if isinstance(item_dump, str):
            return None, item_dump
        assert isinstance(item_dump, Mapping)
        return None, cast(str, item_dump["value"])

    @override
    def _get_key(self, configuration: DummyConfiguration) -> MachineName:
        assert configuration.value
        return configuration.value

    @override
    def _load_key(self, item_dump: Dump, key_dump: str) -> Dump:
        return {"value": key_dump}

    @override
    def _load_item(self, dump: Dump) -> DummyConfiguration:
        raise NotImplementedError


class TestPluginIdentifierKeyConfigurationMapping:
    def test___contains___with_plugin(self) -> None:
        item = DummyConfiguration(DummyPlugin.plugin_id())
        sut = _DummyPluginIdentifierKeyConfigurationMapping([item])
        assert DummyPlugin in sut

    def test___contains___with_plugin_id(self) -> None:
        item = DummyConfiguration(DummyPlugin.plugin_id())
        sut = _DummyPluginIdentifierKeyConfigurationMapping([item])
        assert DummyPlugin.plugin_id() in sut

    def test___getitem___with_plugin(self) -> None:
        item = DummyConfiguration(DummyPlugin.plugin_id())
        sut = _DummyPluginIdentifierKeyConfigurationMapping([item])
        assert sut[DummyPlugin] is item

    def test___getitem___with_plugin_id(self) -> None:
        item = DummyConfiguration(DummyPlugin.plugin_id())
        sut = _DummyPluginIdentifierKeyConfigurationMapping([item])
        assert sut[DummyPlugin.plugin_id()] is item
