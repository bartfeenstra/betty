from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Self

import pytest
from typing_extensions import override

from betty.assertion import RequiredField, assert_int, assert_record
from betty.config import Configuration
from betty.config.collections.sequence import ConfigurationSequence
from betty.test_utils.config.collections.sequence import ConfigurationSequenceTestBase

if TYPE_CHECKING:
    from betty.serde.dump import Dump
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
    def load(cls, dump: Dump, /) -> Self:
        return cls(
            assert_record(
                RequiredField("value", assert_int()),
            )(dump)["value"]
        )

    @override
    def dump(self) -> Dump:
        return {"value": self.value}


class TestConfigurationSequence(
    ConfigurationSequenceTestBase[ConfigurationSequenceTestConfiguration]
):
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
        dump = sut.dump()
        assert dump == []

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
        dump = sut.dump()
        assert isinstance(dump, Sequence)
        assert len(dump) == len(sut_configurations)
        for configuration_key in sut_configuration_keys:
            assert configuration_key < len(dump)


class ConfigurationSequenceTestConfigurationSequence(
    ConfigurationSequence[ConfigurationSequenceTestConfiguration]
):
    @override
    @classmethod
    def _load_item(cls, dump: Dump, /) -> ConfigurationSequenceTestConfiguration:
        return ConfigurationSequenceTestConfiguration.load(dump)
