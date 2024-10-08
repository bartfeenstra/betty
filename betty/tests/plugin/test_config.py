from collections.abc import Iterable
from typing import TYPE_CHECKING

import pytest

from betty.config.collections import ConfigurationCollection
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import ShorthandStaticTranslations
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import MachineName
from betty.plugin.config import (
    PluginConfiguration,
    PluginConfigurationPluginConfigurationMapping,
)
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase

if TYPE_CHECKING:
    from betty.serde.dump import Dump


class TestPluginConfiguration:
    async def test_update(self) -> None:
        sut = PluginConfiguration("hello-world", "")
        other = PluginConfiguration(
            "hello-other-world",
            "Hello, other world!",
            description="Hello, very big other world!",
        )
        sut.update(other)
        assert sut.id == "hello-other-world"
        assert sut.label[UNDETERMINED_LOCALE] == "Hello, other world!"
        assert sut.description[UNDETERMINED_LOCALE] == "Hello, very big other world!"

    async def test_load(self) -> None:
        plugin_id = "hello-world"
        dump: Dump = {
            "id": plugin_id,
            "label": "",
        }
        sut = PluginConfiguration("-", "")
        await sut.load(dump)
        assert sut.id == plugin_id

    async def test_load_with_undetermined_label(self) -> None:
        label = "Hello, world!"
        dump: Dump = {
            "id": "hello-world",
            "label": label,
        }
        sut = PluginConfiguration("-", "")
        await sut.load(dump)
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
        await sut.load(dump)
        assert sut.label[DEFAULT_LOCALIZER.locale] == label

    async def test_load_with_undetermined_description(self) -> None:
        description = "Hello, world!"
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "description": description,
        }
        sut = PluginConfiguration("-", "")
        await sut.load(dump)
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
        await sut.load(dump)
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
    def get_sut(
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

    def get_configurations(
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
