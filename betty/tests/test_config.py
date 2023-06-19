from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable, Generic

import pytest
from reactives.tests import assert_reactor_called, assert_in_scope, assert_scope_empty

from betty.app import App
from betty.config import FileBasedConfiguration, ConfigurationMapping, Configuration, \
    ConfigurationCollection, ConfigurationSequence, ConfigurationKeyT, ConfigurationT
from betty.serde.dump import Dump, VoidableDump
from betty.serde.load import FormatError, Asserter


class TestFileBasedConfiguration:
    def test_configuration_file_path_should_error_unknown_format(self) -> None:
        configuration = FileBasedConfiguration()
        with NamedTemporaryFile(mode='r+', suffix='.abc') as f:
            with pytest.raises(FormatError):
                configuration.configuration_file_path = Path(f.name)


class ConfigurationCollectionTestConfiguration(Configuration, Generic[ConfigurationKeyT]):
    def __init__(self, configuration_key: ConfigurationKeyT, configuration_value: int):
        super().__init__()
        self.key = configuration_key
        self.value = configuration_value


class ConfigurationCollectionTestBase(Generic[ConfigurationKeyT, ConfigurationT]):
    def get_sut(self, configurations: Iterable[ConfigurationT] | None = None) -> ConfigurationCollection[ConfigurationKeyT, ConfigurationT]:
        raise NotImplementedError(repr(self))

    def get_configuration_keys(self) -> tuple[ConfigurationKeyT, ConfigurationKeyT, ConfigurationKeyT, ConfigurationKeyT]:
        raise NotImplementedError(repr(self))

    def get_configurations(self) -> tuple[ConfigurationT, ConfigurationT, ConfigurationT, ConfigurationT]:
        raise NotImplementedError(repr(self))

    def test_getitem(self) -> None:
        configuration = self.get_configurations()[0]
        sut = self.get_sut([configuration])
        with assert_in_scope(sut):
            assert [configuration] == list(sut.values())

    def test_keys(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        with assert_in_scope(sut):
            assert [*self.get_configuration_keys()] == list(sut.keys())

    def test_values(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        with assert_in_scope(sut):
            assert [*configurations] == list(sut.values())

    def test_delitem(self) -> None:
        configuration = self.get_configurations()[0]
        sut = self.get_sut([configuration])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                del sut[self.get_configuration_keys()[0]]
        assert [] == list(sut.values())
        assert [] == list(configuration.react._reactors)

    def test_iter(self) -> None:
        raise NotImplementedError(repr(self))

    def test_len(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([
            configurations[0],
            configurations[1],
        ])
        with assert_in_scope(sut):
            assert 2 == len(sut)

    def test_eq(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([
            configurations[0],
            configurations[1],
        ])
        other = self.get_sut([
            configurations[0],
            configurations[1],
        ])
        with assert_in_scope(sut):
            assert other == sut

    def test_prepend(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([
            configurations[1],
        ])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.prepend(configurations[0])
        assert [configurations[0], configurations[1]] == list(sut.values())
        with assert_reactor_called(sut):
            configurations[0].react.trigger()

    def test_append(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([
            configurations[0],
        ])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.append(configurations[1], configurations[2])
        assert [configurations[0], configurations[1], configurations[2]] == list(sut.values())
        with assert_reactor_called(sut):
            configurations[0].react.trigger()

    def test_insert(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([
            configurations[0],
            configurations[1],
        ])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.insert(1, configurations[2], configurations[3])
        assert [configurations[0], configurations[2], configurations[3], configurations[1]] == list(sut.values())
        with assert_reactor_called(sut):
            configurations[0].react.trigger()

    def test_move_to_beginning(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.move_to_beginning(self.get_configuration_keys()[2], self.get_configuration_keys()[3])
        assert [configurations[2], configurations[3], configurations[0], configurations[1]] == list(sut.values())

    def test_move_towards_beginning(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.move_towards_beginning(self.get_configuration_keys()[2], self.get_configuration_keys()[3])
        assert [configurations[0], configurations[2], configurations[3], configurations[1]] == list(sut.values())

    def test_move_to_end(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.move_to_end(self.get_configuration_keys()[0], self.get_configuration_keys()[1])
        assert [configurations[2], configurations[3], configurations[0], configurations[1]] == list(sut.values())

    def test_move_towards_end(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.move_towards_end(self.get_configuration_keys()[0], self.get_configuration_keys()[1])
        assert [configurations[2], configurations[0], configurations[1], configurations[3]] == list(sut.values())


class ConfigurationSequenceTestBase(Generic[ConfigurationT], ConfigurationCollectionTestBase[int, ConfigurationT]):
    def get_configuration_keys(self) -> tuple[int, int, int, int]:
        return 0, 1, 2, 3

    def test_iter(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([
            configurations[0],
            configurations[1],
        ])
        with assert_in_scope(sut):
            assert [configurations[0], configurations[1]] == list(iter(sut))


class ConfigurationSequenceTestConfigurationSequence(ConfigurationSequence[ConfigurationCollectionTestConfiguration[int]]):
    @classmethod
    def _item_type(cls) -> type[ConfigurationCollectionTestConfiguration[int]]:
        return ConfigurationCollectionTestConfiguration


class TestConfigurationSequence(ConfigurationSequenceTestBase[ConfigurationCollectionTestConfiguration[int]]):
    def get_sut(self, configurations: Iterable[ConfigurationCollectionTestConfiguration[int]] | None = None) -> ConfigurationSequenceTestConfigurationSequence:
        return ConfigurationSequenceTestConfigurationSequence(configurations)

    def get_configurations(self) -> tuple[ConfigurationCollectionTestConfiguration[int], ConfigurationCollectionTestConfiguration[int], ConfigurationCollectionTestConfiguration[int], ConfigurationCollectionTestConfiguration[int]]:
        return (
            ConfigurationCollectionTestConfiguration(self.get_configuration_keys()[0], 123),
            ConfigurationCollectionTestConfiguration(self.get_configuration_keys()[1], 456),
            ConfigurationCollectionTestConfiguration(self.get_configuration_keys()[2], 789),
            ConfigurationCollectionTestConfiguration(self.get_configuration_keys()[0], 000),
        )


class ConfigurationMappingTestBase(Generic[ConfigurationKeyT, ConfigurationT], ConfigurationCollectionTestBase[ConfigurationKeyT, ConfigurationT]):
    def test_iter(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([
            configurations[0],
            configurations[1],
        ])
        with assert_in_scope(sut):
            assert [self.get_configuration_keys()[0], self.get_configuration_keys()[1]] == list(iter(sut))


class ConfigurationMappingTestConfigurationMapping(ConfigurationMapping[str, ConfigurationCollectionTestConfiguration[str]]):
    @classmethod
    def _create_default_item(cls, configuration_key: str) -> ConfigurationCollectionTestConfiguration[str]:
        return ConfigurationCollectionTestConfiguration(configuration_key, 0)

    def _get_key(self, configuration: ConfigurationCollectionTestConfiguration[str]) -> str:
        return configuration.key

    @classmethod
    def _load_key(
        cls,
        item_dump: Dump,
        key_dump: str,
        app: App,
    ) -> Dump:
        asserter = Asserter(localizer=app.localizer)
        dict_item_dump = asserter.assert_dict()(item_dump)
        dict_item_dump[key_dump] = key_dump
        return dict_item_dump

    def _dump_key(
        self,
        item_dump: ConfigurationCollectionItemDumpT,
    ) -> tuple[VoidableDump[ConfigurationCollectionItemDumpT], str]:
        dict_item_dump = self._asserter.assert_dict()(item_dump)
        return dict_item_dump, dict_item_dump.pop('key')


class TestConfigurationMapping(ConfigurationMappingTestBase[str, ConfigurationCollectionTestConfiguration[str]]):
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return 'foo', 'bar', 'baz', 'qux'

    def get_sut(self, configurations: Iterable[ConfigurationCollectionTestConfiguration[str]] | None = None) -> ConfigurationMappingTestConfigurationMapping:
        return ConfigurationMappingTestConfigurationMapping(configurations)

    def get_configurations(self) -> tuple[ConfigurationCollectionTestConfiguration[str], ConfigurationCollectionTestConfiguration[str], ConfigurationCollectionTestConfiguration[str], ConfigurationCollectionTestConfiguration[str]]:
        return (
            ConfigurationCollectionTestConfiguration(self.get_configuration_keys()[0], 123),
            ConfigurationCollectionTestConfiguration(self.get_configuration_keys()[1], 456),
            ConfigurationCollectionTestConfiguration(self.get_configuration_keys()[2], 789),
            ConfigurationCollectionTestConfiguration(self.get_configuration_keys()[3], 000),
        )
