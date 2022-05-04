from __future__ import annotations

import json
import os
from os import path
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Callable, TypeVar, Any, Generic, Optional, TYPE_CHECKING, Union, List, Hashable, \
    Iterable, overload, SupportsIndex

import yaml
from reactives import reactive
from reactives.factory.type import ReactiveInstance

from betty.error import UserFacingError, ContextError, ensure_context
from betty.os import PathLike, ChDir
from betty.typing import Void

if TYPE_CHECKING:
    from betty.builtins import _


class ConfigurationError(UserFacingError, ContextError, ValueError):
    pass


DumpedConfiguration = Union[Any, Void]


@overload
def _minimize_dumped_configuration_collection(dumped_configuration: List, keys: Iterable[SupportsIndex]) -> DumpedConfiguration:
    pass


@overload
def _minimize_dumped_configuration_collection(dumped_configuration: Dict, keys: Iterable[Hashable]) -> DumpedConfiguration:
    pass


def _minimize_dumped_configuration_collection(dumped_configuration, keys) -> DumpedConfiguration:
    for key in keys:
        dumped_configuration[key] = minimize_dumped_configuration(dumped_configuration[key])
        if dumped_configuration[key] is Void:
            del dumped_configuration[key]
    if len(dumped_configuration) > 0:
        return dumped_configuration
    return Void


def minimize_dumped_configuration(configuration: DumpedConfiguration) -> DumpedConfiguration:
    if isinstance(configuration, list):
        return _minimize_dumped_configuration_collection(configuration, reversed(range(len(configuration))))
    if isinstance(configuration, dict):
        return _minimize_dumped_configuration_collection(configuration, list(configuration.keys()))
    return configuration


@reactive
class Configuration(ReactiveInstance):
    def load(self, dumped_configuration: DumpedConfiguration) -> None:
        """
        Validate the dumped configuration and load it into self.

        Raises
        ------
        betty.config.ConfigurationError
        """

        raise NotImplementedError

    def dump(self) -> DumpedConfiguration:
        """
        Dump this configuration to a portable format.
        """

        raise NotImplementedError


ConfigurationT = TypeVar('ConfigurationT', bound=Configuration)


class FileBasedConfiguration(Configuration):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._project_directory: Optional[TemporaryDirectory] = None
        self._configuration_file_path = None
        self._autowrite = False

    def _assert_configuration_file_path(self) -> None:
        if self.configuration_file_path is None:
            raise RuntimeError('The configuration must have a configuration file path.')

    @property
    def autowrite(self) -> bool:
        return self._autowrite

    @autowrite.setter
    def autowrite(self, autowrite: bool) -> None:
        if autowrite:
            self._assert_configuration_file_path()
            if not self._autowrite:
                self.react.react_weakref(self.write)
        else:
            self.react.shutdown(self.write)
        self._autowrite = autowrite

    def write(self, configuration_file_path: Optional[PathLike] = None) -> None:
        if configuration_file_path is None:
            self._assert_configuration_file_path()
        else:
            self.configuration_file_path = configuration_file_path

        self._write(self.configuration_file_path)

    def _write(self, configuration_file_path: Path) -> None:
        # Change the working directory to allow absolute paths to be turned relative to the configuration file's directory
        # path.
        with ChDir(configuration_file_path.parent):
            dumped_configuration = _APP_CONFIGURATION_FORMATS[configuration_file_path.suffix].dumper(self)
            try:
                with open(configuration_file_path, mode='w') as f:
                    f.write(dumped_configuration)
            except FileNotFoundError:
                os.makedirs(configuration_file_path.parent)
                self.write()
        self._configuration_file_path = configuration_file_path

    def read(self, configuration_file_path: Optional[PathLike] = None) -> None:
        if configuration_file_path is None:
            self._assert_configuration_file_path()
        else:
            self.configuration_file_path = configuration_file_path

        # Change the working directory to allow relative paths to be resolved against the configuration file's directory
        # path.
        with ChDir(self.configuration_file_path.parent):
            with ensure_context('in %s' % self.configuration_file_path.resolve()):
                with open(self.configuration_file_path) as f:
                    read_configuration = f.read()
                self.load(_APP_CONFIGURATION_FORMATS[self.configuration_file_path.suffix].loader(read_configuration))

    def __del__(self):
        if hasattr(self, '_project_directory') and self._project_directory is not None:
            self._project_directory.cleanup()

    @reactive  # type: ignore
    @property
    def configuration_file_path(self) -> Path:
        if self._configuration_file_path is None:
            if self._project_directory is None:
                self._project_directory = TemporaryDirectory()
            self._write(Path(self._project_directory.name) / f'{type(self).__name__}.json')
        return self._configuration_file_path  # type: ignore

    @configuration_file_path.setter
    def configuration_file_path(self, configuration_file_path: PathLike) -> None:
        configuration_file_path = Path(configuration_file_path)
        if configuration_file_path == self._configuration_file_path:
            return
        if configuration_file_path.suffix not in _APP_CONFIGURATION_FORMATS:
            raise ConfigurationError(f"Unknown file format \"{configuration_file_path.suffix}\". Supported formats are: {', '.join(APP_CONFIGURATION_FORMATS)}.")
        self._configuration_file_path = configuration_file_path

    @configuration_file_path.deleter
    def configuration_file_path(self) -> None:
        if self._autowrite:
            raise RuntimeError('Cannot remove the configuration file path while autowrite is enabled.')
        self._configuration_file_path = None


class Configurable(Generic[ConfigurationT]):
    def __init__(self, /, configuration: Optional[ConfigurationT] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configuration = configuration

    @property
    def configuration(self) -> ConfigurationT:
        if self._configuration is None:
            raise RuntimeError(f'{self} has no configuration. {type(self)}.__init__() must ensure it is set.')
        return self._configuration


def _from_json(configuration_json: str) -> Any:
    try:
        return json.loads(configuration_json)
    except json.JSONDecodeError as e:
        raise ConfigurationError(_('Invalid JSON: {error}.').format(error=e))


def _from_yaml(configuration_yaml: str) -> Any:
    try:
        return yaml.safe_load(configuration_yaml)
    except yaml.YAMLError as e:
        raise ConfigurationError(_('Invalid YAML: {error}.').format(error=e))


def _to_json(configuration: Configuration) -> str:
    return json.dumps(configuration.dump())


def _to_yaml(configuration: Configuration) -> str:
    return yaml.safe_dump(configuration.dump())


class _Format:
    # These loaders must take a single argument, which is the configuration in its dumped format, as a string. They must
    # return Configuration or raise ConfigurationError.
    Loader = Callable[[str], Any]
    # These dumpers must take a single argument, which is Configuration. They must return a single string.
    Dumper = Callable[[Configuration], str]

    def __init__(self, loader: Loader, dumper: Dumper):
        self.loader = loader
        self.dumper = dumper


_APP_CONFIGURATION_FORMATS: Dict[str, _Format] = {
    '.json': _Format(_from_json, _to_json),
    '.yaml': _Format(_from_yaml, _to_yaml),
    '.yml': _Format(_from_yaml, _to_yaml),
}

APP_CONFIGURATION_FORMATS = set(_APP_CONFIGURATION_FORMATS.keys())


def ensure_path(path_configuration: str) -> Path:
    try:
        return Path(path_configuration).expanduser().resolve()
    except TypeError as e:
        raise ConfigurationError(e)


def ensure_directory_path(path_configuration: str) -> Path:
    ensured_path = ensure_path(path_configuration)
    if not path.isdir(ensured_path):
        raise ConfigurationError(f'"{ensured_path}" is not a directory.')
    return ensured_path
