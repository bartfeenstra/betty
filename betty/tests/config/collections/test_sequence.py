from __future__ import annotations

from typing import Iterable, Self, TYPE_CHECKING

from typing_extensions import override

from betty.assertion import assert_record, RequiredField, assert_int, assert_setattr
from betty.config import Configuration
from betty.config.collections.sequence import ConfigurationSequence
from betty.test_utils.config.collections.sequence import ConfigurationSequenceTestBase

if TYPE_CHECKING:
    from betty.serde.dump import Dump


class ConfigurationSequenceTestConfiguration(Configuration):
    def __init__(self, configuration_value: int):
        super().__init__()
        self.value = configuration_value

    @override
    def update(self, other: Self) -> None:
        pass

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("value", assert_int() | assert_setattr(self, "value")),
        )(dump)

    @override
    def dump(self) -> Dump:
        return {"value": self.value}


class TestConfigurationSequence(
    ConfigurationSequenceTestBase[ConfigurationSequenceTestConfiguration]
):
    def get_sut(
        self,
        configurations: (
            Iterable[ConfigurationSequenceTestConfiguration] | None
        ) = None,
    ) -> ConfigurationSequenceTestConfigurationSequence:
        return ConfigurationSequenceTestConfigurationSequence(configurations)

    def get_configurations(
        self,
    ) -> tuple[
        ConfigurationSequenceTestConfiguration,
        ConfigurationSequenceTestConfiguration,
        ConfigurationSequenceTestConfiguration,
        ConfigurationSequenceTestConfiguration,
    ]:
        return (
            ConfigurationSequenceTestConfiguration(123),
            ConfigurationSequenceTestConfiguration(456),
            ConfigurationSequenceTestConfiguration(789),
            ConfigurationSequenceTestConfiguration(0),
        )

    async def test_load_without_items(self) -> None:
        sut = self.get_sut()
        sut.load([])
        assert len(sut) == 0

    async def test_load_with_items(self) -> None:
        sut = self.get_sut()
        configurations = self.get_configurations()
        sut.load([item.dump() for item in configurations])
        assert len(sut) == len(configurations)


class ConfigurationSequenceTestConfigurationSequence(
    ConfigurationSequence[ConfigurationSequenceTestConfiguration]
):
    @override
    def load_item(self, dump: Dump) -> ConfigurationSequenceTestConfiguration:
        configuration = ConfigurationSequenceTestConfiguration(0)
        configuration.load(dump)
        return configuration