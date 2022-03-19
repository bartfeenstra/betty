from __future__ import annotations

import json
from os import path
from pathlib import Path
from typing import Dict, Callable, Type, TypeVar, Any, Generic

import yaml
from reactives import reactive
from reactives.factory.type import ReactiveInstance

from betty import os
from betty.error import UserFacingError, ContextError, ensure_context


class ConfigurationError(UserFacingError, ContextError, ValueError):
    pass


@reactive
class Configuration(ReactiveInstance):
    def load(self, dumped_configuration: Any) -> None:
        """
        Validate the dumped configuration and load it into self.

        Raises
        ------
        betty.config.ConfigurationError
        """

        raise NotImplementedError

    def dump(self) -> Any:
        """
        Dump this configuration to a portable format.
        """

        raise NotImplementedError

    @classmethod
    def default(cls) -> Configuration:
        return cls()


ConfigurationT = TypeVar('ConfigurationT', bound=Configuration)


class Configurable(Generic[ConfigurationT]):
    def __init__(self, configuration: ConfigurationT, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._configuration = configuration

    @property
    def configuration(self) -> ConfigurationT:
        return self._configuration

    @classmethod
    def configuration_type(cls) -> Type[ConfigurationT]:
        raise NotImplementedError


def from_json(configuration_json: str) -> Any:
    try:
        return json.loads(configuration_json)
    except json.JSONDecodeError as e:
        raise ConfigurationError('Invalid JSON: %s.' % e)


def from_yaml(configuration_yaml: str) -> Any:
    try:
        return yaml.safe_load(configuration_yaml)
    except yaml.YAMLError as e:
        raise ConfigurationError('Invalid YAML: %s' % e)


def from_file(f, configuration: Configuration) -> None:
    file_path = Path(f.name)
    file_extension = file_path.suffix
    try:
        loader = _APP_CONFIGURATION_FORMATS[file_extension].loader
    except KeyError:
        raise ConfigurationError(f"Unknown file format \"{file_extension}\". Supported formats are: {', '.join(APP_CONFIGURATION_FORMATS)}.")
    # Change the working directory to allow relative paths to be resolved against the configuration file's directory
    # path.
    with os.ChDir(Path(f.name).parent):
        with ensure_context('in %s' % file_path.resolve()):
            configuration.load(loader(f.read()))


def to_json(configuration: Configuration) -> str:
    return json.dumps(configuration.dump())


def to_yaml(configuration: Configuration) -> str:
    return yaml.safe_dump(configuration.dump())


def to_file(f, configuration: Configuration) -> None:
    file_base_name, file_extension = path.splitext(f.name)
    try:
        format = _APP_CONFIGURATION_FORMATS[file_extension]
    except KeyError:
        raise ValueError(f"'Unknown file format \"{file_extension}\". Supported formats are: {', '.join(APP_CONFIGURATION_FORMATS)}.'")
    # Change the working directory to allow absolute paths to be turned relative to the configuration file's directory
    # path.
    with os.ChDir(path.dirname(f.name)):
        f.write(format.dumper(configuration))


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
    '.json': _Format(from_json, to_json),
    '.yaml': _Format(from_yaml, to_yaml),
    '.yml': _Format(from_yaml, to_yaml),
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
