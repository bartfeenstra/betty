from __future__ import annotations

import json
from typing import Set, List, Dict

import yaml

from betty.config.dump import DumpedConfiguration, VoidableDumpedConfiguration
from betty.config.load import ConfigurationFormatError
from betty.locale import DEFAULT_LOCALIZER


class Format:
    @property
    def extensions(self) -> Set[str]:
        raise NotImplementedError

    def load(self, dumped_configuration: str) -> DumpedConfiguration:
        raise NotImplementedError

    def dump(self, dumped_configuration: VoidableDumpedConfiguration) -> str:
        raise NotImplementedError


class Json(Format):
    @property
    def extensions(self) -> Set[str]:
        return {'json'}

    def load(self, dumped_configuration: str) -> DumpedConfiguration:
        try:
            return json.loads(dumped_configuration)
        except json.JSONDecodeError as e:
            raise ConfigurationFormatError(DEFAULT_LOCALIZER._('Invalid JSON: {error}.').format(error=e))

    def dump(self, dumped_configuration: VoidableDumpedConfiguration) -> str:
        return json.dumps(dumped_configuration)


class Yaml(Format):
    @property
    def extensions(self) -> Set[str]:
        return {'yaml', 'yml'}

    def load(self, dumped_configuration: str) -> DumpedConfiguration:
        try:
            return yaml.safe_load(dumped_configuration)
        except yaml.YAMLError as e:
            raise ConfigurationFormatError(DEFAULT_LOCALIZER._('Invalid YAML: {error}.').format(error=e))

    def dump(self, dumped_configuration: VoidableDumpedConfiguration) -> str:
        return yaml.safe_dump(dumped_configuration)


FORMATS: List[Format] = [
    Json(),
    Yaml(),
]

FORMATS_BY_EXTENSION: Dict[str, Format] = {
    extension: _format
    for _format in FORMATS
    for extension in _format.extensions
}

EXTENSIONS: List[str] = [
    extension
    for _format in FORMATS
    for extension in _format.extensions
]
