from __future__ import annotations

from typing import Iterable, TYPE_CHECKING, Sequence

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
    async def get_sut(
        self,
        configurations: (
            Iterable[ConfigurationSequenceTestConfiguration] | None
        ) = None,
    ) -> ConfigurationSequenceTestConfigurationSequence:
        return ConfigurationSequenceTestConfigurationSequence(configurations)

    async def get_configurations(
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
        for configuration_key in self.get_configuration_keys():
            assert configuration_key < len(dump)


class ConfigurationSequenceTestConfigurationSequence(
    ConfigurationSequence[ConfigurationSequenceTestConfiguration]
):
    @override
    def _load_item(self, dump: Dump) -> ConfigurationSequenceTestConfiguration:
        configuration = ConfigurationSequenceTestConfiguration(0)
        configuration.load(dump)
        return configuration
