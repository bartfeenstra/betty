from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, Generic, TYPE_CHECKING, TypeVar

import pytest
from typing_extensions import override

from betty.config import (
    FileBasedConfiguration,
    ConfigurationMapping,
    Configuration,
    ConfigurationCollection,
    ConfigurationSequence,
    ConfigurationKey,
)
from betty.assertion import (
    assert_dict,
    assert_record,
    RequiredField,
    assert_str,
    assert_setattr,
    assert_int,
)
from betty.serde.format import FormatError

if TYPE_CHECKING:
    from betty.serde.dump import Dump, VoidableDump


_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)


class TestFileBasedConfiguration:
    async def test_configuration_file_path_should_error_unknown_format(self) -> None:
        configuration = FileBasedConfiguration()
        with (
            NamedTemporaryFile(mode="r+", suffix=".abc") as f,
            pytest.raises(FormatError),
        ):
            configuration.configuration_file_path = Path(f.name)


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


class ConfigurationCollectionTestBase(Generic[_ConfigurationKeyT, _ConfigurationT]):
    def get_sut(
        self, configurations: Iterable[_ConfigurationT] | None = None
    ) -> ConfigurationCollection[_ConfigurationKeyT, _ConfigurationT]:
        raise NotImplementedError(repr(self))

    def get_configuration_keys(
        self,
    ) -> tuple[
        _ConfigurationKeyT, _ConfigurationKeyT, _ConfigurationKeyT, _ConfigurationKeyT
    ]:
        raise NotImplementedError(repr(self))

    def get_configurations(
        self,
    ) -> tuple[_ConfigurationT, _ConfigurationT, _ConfigurationT, _ConfigurationT]:
        raise NotImplementedError(repr(self))

    async def test_replace_without_items(self) -> None:
        sut = self.get_sut()
        sut.clear()
        assert len(sut) == 0
        self.get_configurations()
        sut.replace()
        assert len(sut) == 0

    async def test_replace_with_items(self) -> None:
        sut = self.get_sut()
        sut.clear()
        assert len(sut) == 0
        configurations = self.get_configurations()
        sut.replace(*configurations)
        assert len(sut) == len(configurations)

    async def test_getitem(self) -> None:
        configuration = self.get_configurations()[0]
        sut = self.get_sut([configuration])
        assert [configuration] == list(sut.values())

    async def test_keys(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        assert [*self.get_configuration_keys()] == list(sut.keys())

    async def test_values(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        assert [*configurations] == list(sut.values())

    async def test_delitem(self) -> None:
        configuration = self.get_configurations()[0]
        sut = self.get_sut([configuration])
        del sut[self.get_configuration_keys()[0]]
        assert list(sut.values()) == []

    async def test_iter(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        assert tuple(iter(sut)) == configurations
        assert list(sut.values()) == []

    async def test_len(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        assert len(sut) == 2

    async def test___eq__(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        other = self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        assert other == sut

    async def test_prepend(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(
            [
                configurations[1],
            ]
        )
        sut.prepend(configurations[0])
        assert [configurations[0], configurations[1]] == list(sut.values())

    async def test_append(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(
            [
                configurations[0],
            ]
        )
        sut.append(configurations[1], configurations[2])
        assert [configurations[0], configurations[1], configurations[2]] == list(
            sut.values()
        )

    async def test_insert(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        sut.insert(1, configurations[2], configurations[3])
        assert [
            configurations[0],
            configurations[2],
            configurations[3],
            configurations[1],
        ] == list(sut.values())

    async def test_move_to_beginning(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        sut.move_to_beginning(
            self.get_configuration_keys()[2], self.get_configuration_keys()[3]
        )
        assert [
            configurations[2],
            configurations[3],
            configurations[0],
            configurations[1],
        ] == list(sut.values())

    async def test_move_towards_beginning(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        sut.move_towards_beginning(
            self.get_configuration_keys()[2], self.get_configuration_keys()[3]
        )
        assert [
            configurations[0],
            configurations[2],
            configurations[3],
            configurations[1],
        ] == list(sut.values())

    async def test_move_to_end(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        sut.move_to_end(
            self.get_configuration_keys()[0], self.get_configuration_keys()[1]
        )
        assert [
            configurations[2],
            configurations[3],
            configurations[0],
            configurations[1],
        ] == list(sut.values())

    async def test_move_towards_end(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        sut.move_towards_end(
            self.get_configuration_keys()[0], self.get_configuration_keys()[1]
        )
        assert [
            configurations[2],
            configurations[0],
            configurations[1],
            configurations[3],
        ] == list(sut.values())


class ConfigurationSequenceTestBase(
    Generic[_ConfigurationT], ConfigurationCollectionTestBase[int, _ConfigurationT]
):
    def get_configuration_keys(self) -> tuple[int, int, int, int]:
        return 0, 1, 2, 3

    async def test_iter(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        assert [configurations[0], configurations[1]] == list(iter(sut))


class ConfigurationSequenceTestConfigurationSequence(
    ConfigurationSequence[ConfigurationSequenceTestConfiguration]
):
    @override
    def load_item(self, dump: Dump) -> ConfigurationSequenceTestConfiguration:
        configuration = ConfigurationSequenceTestConfiguration(0)
        configuration.load(dump)
        return configuration


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


class ConfigurationMappingTestBase(
    Generic[_ConfigurationKeyT, _ConfigurationT],
    ConfigurationCollectionTestBase[_ConfigurationKeyT, _ConfigurationT],
):
    async def test_iter(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(
            [
                configurations[0],
                configurations[1],
            ]
        )
        assert [
            self.get_configuration_keys()[0],
            self.get_configuration_keys()[1],
        ] == list(iter(sut))


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

    def _load_key(
        self,
        item_dump: Dump,
        key_dump: str,
    ) -> Dump:
        dict_item_dump = assert_dict()(item_dump)
        dict_item_dump["key"] = key_dump
        return dict_item_dump

    def _dump_key(self, item_dump: VoidableDump) -> tuple[VoidableDump, str]:
        dict_item_dump = assert_dict()(item_dump)
        return dict_item_dump, dict_item_dump.pop("key")


class TestConfigurationMapping(
    ConfigurationMappingTestBase[str, ConfigurationMappingTestConfiguration]
):
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "foo", "bar", "baz", "qux"

    def get_sut(
        self,
        configurations: (Iterable[ConfigurationMappingTestConfiguration] | None) = None,
    ) -> ConfigurationMappingTestConfigurationMapping:
        return ConfigurationMappingTestConfigurationMapping(configurations)

    def get_configurations(
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
        sut = self.get_sut()
        sut.load({})
        assert len(sut) == 0

    async def test_load_with_items(self) -> None:
        sut = self.get_sut()
        configurations = self.get_configurations()
        sut.load({item.key: item.dump() for item in configurations})
        assert len(sut) == len(configurations)
