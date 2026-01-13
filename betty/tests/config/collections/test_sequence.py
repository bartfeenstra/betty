from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Self

import pytest
from typing_extensions import override

from betty.assertion import RequiredField, assert_int, assert_record
from betty.config import Configuration
from betty.config.collections.sequence import ConfigurationSequence
from betty.test_utils.config.collections.sequence import ConfigurationSequenceTestBase

if TYPE_CHECKING:
    from betty.serde import SerializedData
    from betty.test_utils.config.collections import (
        ConfigurationCollectionTestBaseNewSut,
        ConfigurationCollectionTestBaseSutConfigurationKeys,
        ConfigurationCollectionTestBaseSutConfigurations,
    )


class ConfigurationSequenceTestConfiguration(Configuration):
    def __init__(self, value: int, /):
        super().__init__()
        self.value = value

    @override
    @classmethod
    def load(cls, serialized: SerializedData, /) -> Self:
        return cls(
            assert_record(
                RequiredField("value", assert_int()),
            )(serialized)["value"]
        )

    @override
    def dump(self) -> SerializedData:
        return {"value": self.value}

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.value == other.value


class ConfigurationSequenceTestConfigurationSequence(
    ConfigurationSequence[ConfigurationSequenceTestConfiguration]
):
    @override
    @classmethod
    def _item_cls(cls) -> type[ConfigurationSequenceTestConfiguration]:
        return ConfigurationSequenceTestConfiguration


class TestConfigurationSequence(
    ConfigurationSequenceTestBase[
        ConfigurationSequence[ConfigurationSequenceTestConfiguration],
        ConfigurationSequenceTestConfiguration,
    ]
):
    sut_cls = ConfigurationSequence

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        ConfigurationSequenceTestConfiguration, int, int
    ]:
        return ConfigurationSequenceTestConfigurationSequence

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        ConfigurationSequenceTestConfiguration
    ]:
        return (
            ConfigurationSequenceTestConfiguration(123),
            ConfigurationSequenceTestConfiguration(456),
            ConfigurationSequenceTestConfiguration(789),
            ConfigurationSequenceTestConfiguration(0),
        )

    async def test_load__without_items(
        self, sut: ConfigurationSequence[Configuration]
    ) -> None:
        sut = type(sut).load([])
        assert len(sut) == 0

    async def test_load__with_items(
        self,
        sut: ConfigurationSequence[Configuration],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            Configuration
        ],
    ) -> None:
        sut = type(sut).load([item.dump() for item in sut_configurations])
        assert len(sut) == len(sut_configurations)

    async def test_dump__without_items(
        self, sut: ConfigurationSequence[Configuration]
    ) -> None:
        serialized = sut.dump()
        assert serialized == []

    async def test_dump__with_items(
        self,
        sut: ConfigurationSequence[Configuration],
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            Configuration
        ],
        sut_configuration_keys: ConfigurationCollectionTestBaseSutConfigurationKeys[
            int
        ],
    ) -> None:
        sut.replace(*sut_configurations)
        serialized = sut.dump()
        assert isinstance(serialized, Sequence)
        assert len(serialized) == len(sut_configurations)
        for configuration_key in sut_configuration_keys:
            assert configuration_key < len(serialized)
