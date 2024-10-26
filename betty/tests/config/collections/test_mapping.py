from __future__ import annotations

from collections.abc import Sequence, Mapping
from typing import Iterable, TYPE_CHECKING, cast

from typing_extensions import override

from betty.assertion import (
    assert_record,
    RequiredField,
    assert_str,
    assert_setattr,
    assert_int,
)
from betty.config import Configuration
from betty.config.collections.mapping import (
    ConfigurationMapping,
    OrderedConfigurationMapping,
)
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase

if TYPE_CHECKING:
    from betty.serde.dump import Dump


class ConfigurationMappingTestConfiguration(Configuration):
    def __init__(self, configuration_key: str, configuration_value: int):
        super().__init__()
        self.key = configuration_key
        self.value = configuration_value

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("key", assert_str() | assert_setattr(self, "key")),
            RequiredField("value", assert_int() | assert_setattr(self, "value")),
        )(dump)

    @override
    def dump(self) -> Dump:
        return {
            "key": self.key,
            "value": self.value,
        }


class TestConfigurationMapping(
    ConfigurationMappingTestBase[str, ConfigurationMappingTestConfiguration]
):
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "foo", "bar", "baz", "qux"

    async def get_sut(
        self,
        configurations: (Iterable[ConfigurationMappingTestConfiguration] | None) = None,
    ) -> ConfigurationMappingTestConfigurationMapping:
        return ConfigurationMappingTestConfigurationMapping(configurations)

    async def get_configurations(
        self,
    ) -> tuple[
        ConfigurationMappingTestConfiguration,
        ConfigurationMappingTestConfiguration,
        ConfigurationMappingTestConfiguration,
        ConfigurationMappingTestConfiguration,
    ]:
        return (
            ConfigurationMappingTestConfiguration(
                self.get_configuration_keys()[0], 123
            ),
            ConfigurationMappingTestConfiguration(
                self.get_configuration_keys()[1], 456
            ),
            ConfigurationMappingTestConfiguration(
                self.get_configuration_keys()[2], 789
            ),
            ConfigurationMappingTestConfiguration(
                self.get_configuration_keys()[3], 000
            ),
        )

    async def test_load_without_items(self) -> None:
        sut = await self.get_sut()
        sut.load({})
        assert len(sut) == 0

    async def test_load_with_items(self) -> None:
        sut = await self.get_sut()
        configurations = await self.get_configurations()
        sut.load({item.key: item.dump() for item in configurations})
        assert len(sut) == len(configurations)

    async def test_dump_without_items(self) -> None:
        sut = await self.get_sut()
        dump = sut.dump()
        assert dump == {}

    async def test_dump_with_items(self) -> None:
        configurations = await self.get_configurations()
        sut = await self.get_sut()
        sut.replace(*configurations)
        dump = sut.dump()
        assert isinstance(dump, Mapping)
        assert len(dump) == len(configurations)
        for configuration_key in self.get_configuration_keys():
            assert configuration_key in dump


class ConfigurationMappingTestConfigurationMapping(
    ConfigurationMapping[str, ConfigurationMappingTestConfiguration]
):
    @override
    def load_item(self, dump: Dump) -> ConfigurationMappingTestConfiguration:
        configuration = ConfigurationMappingTestConfiguration("", 0)
        configuration.load(dump)
        return configuration

    def _get_key(self, configuration: ConfigurationMappingTestConfiguration) -> str:
        return configuration.key

    def _load_key(self, item_dump: Dump, key_dump: str) -> Dump:
        assert isinstance(item_dump, Mapping)
        item_dump["key"] = key_dump
        return item_dump

    def _dump_key(self, item_dump: Dump) -> tuple[Dump, str]:
        assert isinstance(item_dump, Mapping)
        return item_dump, cast(str, item_dump.pop("key"))


class TestOrderedConfigurationMapping(
    ConfigurationMappingTestBase[str, ConfigurationMappingTestConfiguration]
):
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "foo", "bar", "baz", "qux"

    async def get_sut(
        self,
        configurations: (Iterable[ConfigurationMappingTestConfiguration] | None) = None,
    ) -> OrderedConfigurationMappingTestOrderedConfigurationMapping:
        return OrderedConfigurationMappingTestOrderedConfigurationMapping(
            configurations
        )

    async def get_configurations(
        self,
    ) -> tuple[
        ConfigurationMappingTestConfiguration,
        ConfigurationMappingTestConfiguration,
        ConfigurationMappingTestConfiguration,
        ConfigurationMappingTestConfiguration,
    ]:
        return (
            ConfigurationMappingTestConfiguration(
                self.get_configuration_keys()[0], 123
            ),
            ConfigurationMappingTestConfiguration(
                self.get_configuration_keys()[1], 456
            ),
            ConfigurationMappingTestConfiguration(
                self.get_configuration_keys()[2], 789
            ),
            ConfigurationMappingTestConfiguration(
                self.get_configuration_keys()[3], 000
            ),
        )

    async def test_load_without_items(self) -> None:
        sut = await self.get_sut()
        sut.load([])
        assert len(sut) == 0

    async def test_load_with_items(self) -> None:
        sut = await self.get_sut()
        configurations = await self.get_configurations()
        sut.load([item.dump() for item in configurations])
        assert len(sut) == len(configurations)

    async def test_dump_without_items(self) -> None:
        sut = await self.get_sut()
        dump = sut.dump()
        assert dump == []

    async def test_dump_with_items(self) -> None:
        configurations = await self.get_configurations()
        sut = await self.get_sut()
        sut.replace(*configurations)
        dump = sut.dump()
        assert isinstance(dump, Sequence)
        assert len(dump) == len(configurations)


class OrderedConfigurationMappingTestOrderedConfigurationMapping(
    OrderedConfigurationMapping[str, ConfigurationMappingTestConfiguration]
):
    @override
    def load_item(self, dump: Dump) -> ConfigurationMappingTestConfiguration:
        configuration = ConfigurationMappingTestConfiguration("", 0)
        configuration.load(dump)
        return configuration

    @override
    def _get_key(self, configuration: ConfigurationMappingTestConfiguration) -> str:
        return configuration.key
