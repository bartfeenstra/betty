from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterator, Type, Union, Optional, Tuple, Iterable, List, Any, overload, Generic

import pytest
from reactives.tests import assert_reactor_called, assert_in_scope, assert_scope_empty

from betty.app import App
from betty.config import FileBasedConfiguration, ConfigurationMapping, Configuration, VoidableDumpedConfiguration, \
    DumpedConfiguration, ConfigurationCollection, ConfigurationSequence, ConfigurationKeyT, ConfigurationT
from betty.config.error import ConfigurationError, ConfigurationErrorCollection
from betty.config.load import ConfigurationFormatError, Asserter
from betty.locale import Localizer


class ConfigurationAssertionError(AssertionError):
    pass


@overload
def assert_configuration_error(
        actual_error: Union[ConfigurationError, ConfigurationErrorCollection],
        *,
        error: ConfigurationError,
        error_type: None = None,
        error_message: None = None,
        error_contexts: None = None,
) -> List[ConfigurationError]:
    pass


@overload
def assert_configuration_error(
        actual_error: Union[ConfigurationError, ConfigurationErrorCollection],
        *,
        error: None = None,
        error_type: Type[ConfigurationError] = ConfigurationError,
        error_message: str | None = None,
        error_contexts: Tuple[str, ...] | None = None,
) -> List[ConfigurationError]:
    pass


def assert_configuration_error(
        actual_error: Union[ConfigurationError, ConfigurationErrorCollection],
        *,
        error: ConfigurationError | None = None,
        error_type: Type[ConfigurationError] | None = ConfigurationError,
        error_message: str | None = None,
        error_contexts: Tuple[str, ...] | None = None,
) -> List[ConfigurationError]:
    actual_errors: Iterable[ConfigurationError]
    if isinstance(actual_error, ConfigurationErrorCollection):
        actual_errors = [*actual_error]
    else:
        actual_errors = [actual_error]

    expected_error_type: type
    expected_error_message = None
    expected_error_contexts = None
    if error:
        expected_error_type = type(error)
        expected_error_message = str(error)
        expected_error_contexts = error.contexts
    else:
        expected_error_type = error_type  # type: ignore[assignment]
        if error_message is not None:
            expected_error_message = error_message
        if error_contexts is not None:
            expected_error_contexts = error_contexts

    errors = [actual_error for actual_error in actual_errors if isinstance(actual_error, expected_error_type)]
    if expected_error_message is not None:
        errors = [actual_error for actual_error in actual_errors if str(actual_error).startswith(expected_error_message)]
    if expected_error_contexts is not None:
        errors = [actual_error for actual_error in actual_errors if expected_error_contexts == actual_error.contexts]
    if errors:
        return errors
    raise ConfigurationAssertionError('Failed raising a configuration error.')


@contextmanager
def raises_configuration_error(*args, **kwargs) -> Iterator[ConfigurationErrorCollection]:
    try:
        with App():
            with ConfigurationErrorCollection().catch() as errors:
                yield errors
    finally:
        assert_configuration_error(errors, *args, **kwargs)
        errors.assert_valid()


class TestFileBasedConfiguration:
    def test_configuration_file_path_should_error_unknown_format(self) -> None:
        configuration = FileBasedConfiguration()
        with NamedTemporaryFile(mode='r+', suffix='.abc') as f:
            with pytest.raises(ConfigurationFormatError):
                configuration.configuration_file_path = Path(f.name)


class ConfigurationCollectionTestConfiguration(Configuration):
    def __init__(self, configuration_key: Any, configuration_value: int):
        super().__init__()
        self.key = configuration_key
        self.value = configuration_value


class ConfigurationCollectionTestBase(Generic[ConfigurationKeyT, ConfigurationT]):
    def get_sut(self, configurations: Optional[Iterable[ConfigurationT]] = None) -> ConfigurationCollection[ConfigurationKeyT, ConfigurationT]:
        raise NotImplementedError

    def get_configuration_keys(self) -> Tuple[ConfigurationKeyT, ConfigurationKeyT, ConfigurationKeyT, ConfigurationKeyT]:
        raise NotImplementedError

    def get_configurations(self) -> Tuple[ConfigurationT, ConfigurationT, ConfigurationT, ConfigurationT]:
        raise NotImplementedError

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
        raise NotImplementedError

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
    def get_configuration_keys(self) -> Tuple[int, int, int, int]:
        return 0, 1, 2, 3

    def test_iter(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([
            configurations[0],
            configurations[1],
        ])
        with assert_in_scope(sut):
            assert [configurations[0], configurations[1]] == list(iter(sut))


class ConfigurationSequenceTestConfigurationSequence(ConfigurationSequence[ConfigurationCollectionTestConfiguration]):
    @classmethod
    def _item_type(cls) -> Type[ConfigurationCollectionTestConfiguration]:
        return ConfigurationCollectionTestConfiguration


class TestConfigurationSequence(ConfigurationSequenceTestBase[ConfigurationCollectionTestConfiguration]):
    def get_sut(self, configurations: Optional[Iterable[ConfigurationCollectionTestConfiguration]] = None) -> ConfigurationSequenceTestConfigurationSequence:
        return ConfigurationSequenceTestConfigurationSequence(configurations)

    def get_configurations(self) -> Tuple[ConfigurationCollectionTestConfiguration, ConfigurationCollectionTestConfiguration, ConfigurationCollectionTestConfiguration, ConfigurationCollectionTestConfiguration]:
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


class ConfigurationMappingTestConfigurationMapping(ConfigurationMapping[str, ConfigurationCollectionTestConfiguration]):
    @classmethod
    def _create_default_item(cls, configuration_key: ConfigurationKeyT) -> ConfigurationCollectionTestConfiguration:
        return ConfigurationCollectionTestConfiguration(configuration_key, 0)

    def _get_key(self, configuration: ConfigurationCollectionTestConfiguration) -> str:
        return configuration.key

    @classmethod
    def _load_key(
        cls,
        dumped_item: DumpedConfiguration,
        dumped_key: str,
        *,
        localizer: Localizer | None = None,
    ) -> DumpedConfiguration:
        asserter = Asserter(localizer=localizer)
        dumped_dict = asserter.assert_dict()(dumped_item)
        dumped_dict[dumped_key] = dumped_key
        return dumped_dict

    def _dump_key(self, dumped_item: VoidableDumpedConfiguration) -> Tuple[VoidableDumpedConfiguration, str]:
        dumped_dict = self._asserter.assert_dict()(dumped_item)
        return dumped_dict, dumped_dict.pop('key')


class TestConfigurationMapping(ConfigurationMappingTestBase[str, ConfigurationCollectionTestConfiguration]):
    def get_configuration_keys(self) -> Tuple[str, str, str, str]:
        return 'foo', 'bar', 'baz', 'qux'

    def get_sut(self, configurations: Optional[Iterable[ConfigurationCollectionTestConfiguration]] = None) -> ConfigurationMappingTestConfigurationMapping:
        return ConfigurationMappingTestConfigurationMapping(configurations)

    def get_configurations(self) -> Tuple[ConfigurationCollectionTestConfiguration, ConfigurationCollectionTestConfiguration, ConfigurationCollectionTestConfiguration, ConfigurationCollectionTestConfiguration]:
        return (
            ConfigurationCollectionTestConfiguration(self.get_configuration_keys()[0], 123),
            ConfigurationCollectionTestConfiguration(self.get_configuration_keys()[1], 456),
            ConfigurationCollectionTestConfiguration(self.get_configuration_keys()[2], 789),
            ConfigurationCollectionTestConfiguration(self.get_configuration_keys()[3], 000),
        )
