from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Self

import pytest
from typing_extensions import override

from betty.assertion import RequiredField, assert_int, assert_record, assert_str
from betty.config import Configuration
from betty.config.collections.mapping import OrderedConfigurationMapping
from betty.test_utils.config.collections.mapping import (
    OrderedConfigurationMappingTestBase,
)

if TYPE_CHECKING:
    from betty.portable import PortableData
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
    def load(cls, portable: PortableData, /) -> Self:
        record = assert_record(
            RequiredField("key", assert_str()),
            RequiredField("value", assert_int()),
        )(portable)
        return cls(record["key"], record["value"])

    @override
    def dump(self) -> PortableData:
        return {
            "key": self.key,
            "value": self.value,
        }

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.key, self.value) == (other.key, other.value)


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
    OrderedConfigurationMappingTestBase[
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
        portable = sut.dump()
        assert portable == []

    async def test_dump__with_items(
        self,
        sut: OrderedConfigurationMapping[str, str, Configuration],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            ConfigurationMappingTestConfiguration
        ],
    ) -> None:
        sut.replace(*sut_configurations)
        portable = sut.dump()
        assert isinstance(portable, Sequence)
        assert len(portable) == len(sut_configurations)
