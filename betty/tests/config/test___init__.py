from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Iterator, Type, Union, Optional, Tuple, Iterable, List, Any

import pytest
from reactives.tests import assert_reactor_called, assert_in_scope, assert_scope_empty

from betty.app import App
from betty.config import FileBasedConfiguration, ConfigurationMapping, Configuration, DumpedConfigurationExport, \
    DumpedConfigurationImport
from betty.config.error import ConfigurationError, ConfigurationErrorCollection
from betty.config.load import ConfigurationFormatError, Loader


class ConfigurationAssertionError(AssertionError):
    pass


def assert_configuration_error(
        actual_error: Union[ConfigurationError, ConfigurationErrorCollection],
        error: Optional[Union[ConfigurationError, Type[ConfigurationError]]] = None,
        error_type: Optional[Type[ConfigurationError]] = None,
        error_message: Optional[str] = None,
        error_contexts: Optional[Tuple[str, ...]] = None,
) -> List[ConfigurationError]:
    actual_errors: Iterable[ConfigurationError]
    if isinstance(actual_error, ConfigurationErrorCollection):
        actual_errors = actual_error.flatten()
    else:
        actual_errors = [actual_error]

    expected_error_type = None
    expected_error_message = None
    expected_error_contexts = None
    if error:
        expected_error_type = type(error)
        expected_error_message = str(error)
        expected_error_contexts = error.contexts
    if error_type:
        expected_error_type = error_type
    if not expected_error_type:
        expected_error_type = ConfigurationError
    if error_message:
        expected_error_message = error_message
    if error_type:
        expected_error_contexts = error_contexts

    errors = [
        actual_error
        for actual_error
        in actual_errors
        if isinstance(actual_error, expected_error_type) or expected_error_message and str(actual_error).startswith(expected_error_message) or expected_error_contexts and expected_error_contexts == actual_error.contexts
    ]
    if errors:
        return errors
    raise ConfigurationAssertionError('Failed raising a configuration error.')


@contextmanager
def raises_configuration_error(*args, **kwargs) -> Iterator[Loader]:
    loader = Loader()
    try:
        with App():
            yield loader
            if loader.errors.valid:
                loader.commit()
    finally:
        assert_configuration_error(loader.errors, *args, **kwargs)


@contextmanager
def raises_no_configuration_errors(*args, **kwargs) -> Iterator[Loader]:
    loader = Loader()
    try:
        with App():
            yield loader
            loader.commit()
    finally:
        try:
            errors = assert_configuration_error(loader.errors, *args, **kwargs)
        except ConfigurationAssertionError:
            return
        raise ConfigurationAssertionError('Failed not to raise a configuration error') from errors[0]


class TestFileBasedConfiguration:
    def test_configuration_file_path_should_error_unknown_format(self) -> None:
        configuration = FileBasedConfiguration()
        with NamedTemporaryFile(mode='r+', suffix='.abc') as f:
            with pytest.raises(ConfigurationFormatError):
                configuration.configuration_file_path = f.name  # type: ignore[assignment]


class ConfigurationMappingTestDummyConfiguration(Configuration):
    def __init__(self, configuration_key: str, configuration_value: int):
        super().__init__()
        self.key = configuration_key
        self.value = configuration_value

    def load(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> None:
        raise NotImplementedError

    def dump(self) -> DumpedConfigurationExport:
        raise NotImplementedError


class ConfigurationMappingTestDummy(ConfigurationMapping[str, ConfigurationMappingTestDummyConfiguration]):
    def _get_key(self, configuration: ConfigurationMappingTestDummyConfiguration) -> str:
        return configuration.key

    def _load_key(self, dumped_configuration_key: str) -> str:
        return dumped_configuration_key

    def _dump_key(self, configuration_key: str) -> str:
        return configuration_key

    def _default_configuration_item(self, configuration_key: str) -> ConfigurationMappingTestDummyConfiguration:
        return ConfigurationMappingTestDummyConfiguration('foo', 123)


class TestConfigurationMapping:
    def test_getitem(self) -> None:
        configuration = ConfigurationMappingTestDummyConfiguration('foo', 123)
        sut = ConfigurationMappingTestDummy([configuration])
        with assert_in_scope(sut):
            assert configuration == sut['foo']

    def test_delitem(self) -> None:
        configuration = ConfigurationMappingTestDummyConfiguration('foo', 123)
        sut = ConfigurationMappingTestDummy([configuration])
        with assert_scope_empty():
            with assert_reactor_called(sut):
                del sut['foo']
        assert [] == list(sut)
        assert [] == list(configuration.react._reactors)

    def test_iter(self) -> None:
        configuration_a = ConfigurationMappingTestDummyConfiguration('foo', 123)
        configuration_b = ConfigurationMappingTestDummyConfiguration('bar', 456)
        sut = ConfigurationMappingTestDummy([
            configuration_a,
            configuration_b,
        ])
        with assert_in_scope(sut):
            assert [configuration_a, configuration_b] == list(iter(sut))

    def test_len(self) -> None:
        configuration_a = ConfigurationMappingTestDummyConfiguration('foo', 123)
        configuration_b = ConfigurationMappingTestDummyConfiguration('bar', 456)
        sut = ConfigurationMappingTestDummy([
            configuration_a,
            configuration_b,
        ])
        with assert_in_scope(sut):
            assert 2 == len(sut)

    def test_eq(self) -> None:
        configuration_a = ConfigurationMappingTestDummyConfiguration('foo', 123)
        configuration_b = ConfigurationMappingTestDummyConfiguration('bar', 456)
        sut = ConfigurationMappingTestDummy([
            configuration_a,
            configuration_b,
        ])
        other = ConfigurationMappingTestDummy([
            configuration_a,
            configuration_b,
        ])
        with assert_in_scope(sut):
            assert other == sut

    def test_add(self) -> None:
        sut = ConfigurationMappingTestDummy()
        configuration = ConfigurationMappingTestDummyConfiguration('foo', 123)
        with assert_scope_empty():
            with assert_reactor_called(sut):
                sut.add(configuration)
        assert configuration == sut['foo']
        with assert_reactor_called(sut):
            configuration.react.trigger()


class ConfigurationCollectionMappingTestBase:
    def test(self) -> None:
        sut = self.get_sut()
        configuration_key = self.get_configuration_key()
        configuration = sut._default_configuration_item(configuration_key)
        assert isinstance(configuration, Configuration)
        assert configuration_key == sut._get_key(configuration)
        dumped_configuration_key = sut._dump_key(configuration_key)
        assert isinstance(dumped_configuration_key, str)
        loaded_configuration_key = sut._load_key(dumped_configuration_key)
        assert configuration_key == loaded_configuration_key

    def get_sut(self) -> ConfigurationMapping:
        raise NotImplementedError

    def get_configuration_key(self) -> Any:
        raise NotImplementedError
