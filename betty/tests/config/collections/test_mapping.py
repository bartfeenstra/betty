from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Self, cast

import pytest
from typing_extensions import override

from betty.assertion import RequiredField, assert_int, assert_record, assert_str
from betty.config import Configuration
from betty.config.collections.mapping import (
    ConfigurationMapping,
    OrderedConfigurationMapping,
)
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase

if TYPE_CHECKING:
    from betty.serde import SerializedData
    from betty.test_utils.config.collections import (
        ConfigurationCollectionTestBaseNewSut,
        ConfigurationCollectionTestBaseSutConfigurationKeys,
        ConfigurationCollectionTestBaseSutConfigurations,
    )


class ConfigurationMappingTestConfiguration(Configuration):
    def __init__(self, key: str, value: int, /):
        super().__init__()
        self.key = key
        self.value = value

    @override
    @classmethod
    def load(cls, serialized: SerializedData, /) -> Self:
        record = assert_record(
            RequiredField("key", assert_str()),
            RequiredField("value", assert_int()),
        )(serialized)
        return cls(record["key"], record["value"])

    @override
    def dump(self) -> SerializedData:
        return {
            "key": self.key,
            "value": self.value,
        }

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.key, self.value) == (other.key, other.value)


class ConfigurationMappingTestConfigurationMapping(
    ConfigurationMapping[str, str, ConfigurationMappingTestConfiguration]
):
    @override
    def _resolve_key(self, configuration_key: str, /) -> str:
        return configuration_key

    @override
    @classmethod
    def _item_cls(cls) -> type[ConfigurationMappingTestConfiguration]:
        return ConfigurationMappingTestConfiguration

    @override
    def _get_key(self, configuration: ConfigurationMappingTestConfiguration, /) -> str:
        return configuration.key

    @override
    @classmethod
    def _load_key(
        cls, serialized_item: SerializedData, serialized_key: str, /
    ) -> SerializedData:
        assert isinstance(serialized_item, Mapping)
        serialized_item["key"] = serialized_key
        return serialized_item

    @override
    def _dump_key(
        self, serialized_item: SerializedData, /
    ) -> tuple[SerializedData, str]:
        assert isinstance(serialized_item, Mapping)
        return serialized_item, cast(str, serialized_item.pop("key"))


class TestConfigurationMapping(
    ConfigurationMappingTestBase[
        ConfigurationMapping[str, str, ConfigurationMappingTestConfiguration],
        str,
        str,
        ConfigurationMappingTestConfiguration,
    ]
):
    sut_cls = ConfigurationMapping

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[str]:
        return "foo", "bar", "baz", "qux"

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        ConfigurationMappingTestConfiguration, str, str
    ]:
        return ConfigurationMappingTestConfigurationMapping

    @override
    @pytest.fixture
    def sut_configurations(
        self,
        sut_configuration_keys: ConfigurationCollectionTestBaseSutConfigurationKeys[
            str
        ],
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        ConfigurationMappingTestConfiguration
    ]:
        return (
            ConfigurationMappingTestConfiguration(sut_configuration_keys[0], 123),
            ConfigurationMappingTestConfiguration(sut_configuration_keys[1], 456),
            ConfigurationMappingTestConfiguration(sut_configuration_keys[2], 789),
            ConfigurationMappingTestConfiguration(sut_configuration_keys[3], 000),
        )

    async def test_load__without_items(
        self, sut: ConfigurationMapping[str, str, Configuration]
    ) -> None:
        sut = type(sut).load({})
        assert len(sut) == 0

    async def test_load__with_items(
        self,
        sut: ConfigurationMapping[str, str, Configuration],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            ConfigurationMappingTestConfiguration
        ],
    ) -> None:
        sut = type(sut).load({item.key: item.dump() for item in sut_configurations})
        assert len(sut) == len(sut_configurations)

    async def test_dump__without_items(
        self, sut: ConfigurationMapping[str, str, Configuration]
    ) -> None:
        serialized = sut.dump()
        assert serialized == {}

    async def test_dump__with_items(
        self,
        sut: ConfigurationMapping[str, str, Configuration],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            ConfigurationMappingTestConfiguration
        ],
        sut_configuration_keys: ConfigurationCollectionTestBaseSutConfigurationKeys[
            str
        ],
    ) -> None:
        sut.replace(*sut_configurations)
        serialized = sut.dump()
        assert isinstance(serialized, Mapping)
        assert len(serialized) == len(sut_configurations)
        for configuration_key in sut_configuration_keys:
            assert configuration_key in serialized


class OrderedConfigurationMappingTestOrderedConfigurationMapping(
    OrderedConfigurationMapping[str, str, ConfigurationMappingTestConfiguration]
):
    @override
    def _resolve_key(self, configuration_key: str, /) -> str:
        return configuration_key

    @override
    @classmethod
    def _item_cls(cls) -> type[ConfigurationMappingTestConfiguration]:
        return ConfigurationMappingTestConfiguration

    @override
    def _get_key(self, configuration: ConfigurationMappingTestConfiguration, /) -> str:
        return configuration.key


class TestOrderedConfigurationMapping(
    ConfigurationMappingTestBase[
        OrderedConfigurationMapping[str, str, ConfigurationMappingTestConfiguration],
        str,
        str,
        ConfigurationMappingTestConfiguration,
    ]
):
    sut_cls = OrderedConfigurationMapping

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[str]:
        return "foo", "bar", "baz", "qux"

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        ConfigurationMappingTestConfiguration, str, str
    ]:
        return OrderedConfigurationMappingTestOrderedConfigurationMapping

    @override
    @pytest.fixture
    def sut_configurations(
        self,
        sut_configuration_keys: ConfigurationCollectionTestBaseSutConfigurationKeys[
            str
        ],
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        ConfigurationMappingTestConfiguration
    ]:
        return (
            ConfigurationMappingTestConfiguration(sut_configuration_keys[0], 123),
            ConfigurationMappingTestConfiguration(sut_configuration_keys[1], 456),
            ConfigurationMappingTestConfiguration(sut_configuration_keys[2], 789),
            ConfigurationMappingTestConfiguration(sut_configuration_keys[3], 000),
        )

    async def test_load__without_items(
        self, sut: OrderedConfigurationMapping[str, str, Configuration]
    ) -> None:
        sut = type(sut).load([])
        assert len(sut) == 0

    async def test_load__with_items(
        self,
        sut: OrderedConfigurationMapping[str, str, Configuration],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            ConfigurationMappingTestConfiguration
        ],
    ) -> None:
        sut = type(sut).load([item.dump() for item in sut_configurations])
        assert len(sut) == len(sut_configurations)

    async def test_dump__without_items(
        self, sut: OrderedConfigurationMapping[str, str, Configuration]
    ) -> None:
        serialized = sut.dump()
        assert serialized == []

    async def test_dump__with_items(
        self,
        sut: OrderedConfigurationMapping[str, str, Configuration],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            ConfigurationMappingTestConfiguration
        ],
    ) -> None:
        sut.replace(*sut_configurations)
        serialized = sut.dump()
        assert isinstance(serialized, Sequence)
        assert len(serialized) == len(sut_configurations)
