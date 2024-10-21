from collections.abc import Iterable

import pytest
from typing_extensions import override

from betty.assertion import assert_record, RequiredField, assert_bool, assert_setattr
from betty.assertion.error import AssertionFailed
from betty.config import Configuration, DefaultConfigurable
from betty.config.collections import ConfigurationCollection
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import ShorthandStaticTranslations
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import MachineName
from betty.plugin.config import (
    PluginConfiguration,
    PluginConfigurationPluginConfigurationMapping,
    PluginInstanceConfiguration,
)
from betty.plugin.static import StaticPluginRepository
from betty.serde.dump import Dump
from betty.test_utils.assertion.error import raises_error
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase
from betty.test_utils.plugin import DummyPlugin


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
    class _DummyDefaultConfigurablePluginConfiguration(Configuration):
        def __init__(self, *, check: bool = False):
            super().__init__()
            self.check = check

        @override
        def load(self, dump: Dump) -> None:
            assert_record(
                RequiredField("check", assert_bool() | assert_setattr(self, "check"))
            )(dump)

        @override
        def dump(self) -> Dump:
            return {
                "check": self.check,
            }

    class _DummyDefaultConfigurablePlugin(
        DefaultConfigurable[_DummyDefaultConfigurablePluginConfiguration], DummyPlugin
    ):
        @override
        @classmethod
        def new_default_configuration(
            cls,
        ) -> "TestPluginInstanceConfiguration._DummyDefaultConfigurablePluginConfiguration":
            return TestPluginInstanceConfiguration._DummyDefaultConfigurablePluginConfiguration()

    def test___init___with_configuration_without_configurable_plugin_should_error(self):
        plugin = DummyPlugin
        with pytest.raises(ValueError):  # noqa PT011
            PluginInstanceConfiguration(
                plugin,
                plugin_repository=StaticPluginRepository(plugin),
                plugin_configuration=self._DummyDefaultConfigurablePluginConfiguration(),
            )

    def test_plugin(self) -> None:
        plugin = DummyPlugin
        sut = PluginInstanceConfiguration(
            plugin, plugin_repository=StaticPluginRepository(plugin)
        )
        assert sut.plugin == plugin

    def test_plugin_configuration(self) -> None:
        plugin = self._DummyDefaultConfigurablePlugin
        plugin_configuration = self._DummyDefaultConfigurablePluginConfiguration()
        sut = PluginInstanceConfiguration(
            plugin,
            plugin_configuration=plugin_configuration,
            plugin_repository=StaticPluginRepository(plugin),
        )
        assert sut.plugin_configuration is plugin_configuration

    def test_load_without_id(self) -> None:
        plugin = DummyPlugin
        with raises_error(error_type=AssertionFailed):
            (
                PluginInstanceConfiguration(
                    plugin, plugin_repository=StaticPluginRepository(plugin)
                )
            ).load({})

    def test_load_minimal(self) -> None:
        plugin = DummyPlugin
        sut = PluginInstanceConfiguration(
            plugin, plugin_repository=StaticPluginRepository(plugin)
        )
        sut.load({"id": DummyPlugin.plugin_id()})
        assert sut.plugin == DummyPlugin

    def test_load_with_configuration(self) -> None:
        plugin = self._DummyDefaultConfigurablePlugin
        sut = PluginInstanceConfiguration(
            plugin, plugin_repository=StaticPluginRepository(plugin)
        )
        sut.load(
            {
                "id": self._DummyDefaultConfigurablePlugin.plugin_id(),
                "configuration": {
                    "check": True,
                },
            }
        )
        plugin_configuration = sut.plugin_configuration
        assert isinstance(
            plugin_configuration, self._DummyDefaultConfigurablePluginConfiguration
        )
        assert plugin_configuration.check

    def test_load_with_configuration_for_non_configurable_plugin_should_error(
        self,
    ) -> None:
        plugin = DummyPlugin
        sut = PluginInstanceConfiguration(
            plugin, plugin_repository=StaticPluginRepository(plugin)
        )
        with pytest.raises(AssertionFailed):
            sut.load(
                {
                    "id": DummyPlugin.plugin_id(),
                    "configuration": {},
                }
            )

    def test_dump_should_dump_minimal(self) -> None:
        plugin = DummyPlugin
        sut = PluginInstanceConfiguration(
            plugin, plugin_repository=StaticPluginRepository(plugin)
        )
        expected = {
            "id": DummyPlugin.plugin_id(),
        }
        assert sut.dump() == expected

    def test_dump_should_dump_plugin_configuration(self) -> None:
        plugin = self._DummyDefaultConfigurablePlugin
        sut = PluginInstanceConfiguration(
            plugin, plugin_repository=StaticPluginRepository(plugin)
        )
        expected = {
            "id": self._DummyDefaultConfigurablePlugin.plugin_id(),
            "configuration": {
                "check": False,
            },
        }
        assert sut.dump() == expected
