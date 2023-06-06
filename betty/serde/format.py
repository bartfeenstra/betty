from __future__ import annotations

import json
from typing import cast

import yaml

from betty.locale import Localizable, Localizer
from betty.serde.dump import Dump, VoidableDump
from betty.serde.load import FormatError


class Format(Localizable):
    @property
    def extensions(self) -> set[str]:
        raise NotImplementedError(repr(self))

    @property
    def label(self) -> str:
        raise NotImplementedError(repr(self))

    def load(self, dump: str) -> Dump:
        raise NotImplementedError(repr(self))

    def dump(self, dump: VoidableDump[Dump]) -> str:
        raise NotImplementedError(repr(self))


class Json(Format):
    @property
    def extensions(self) -> set[str]:
        return {'json'}

    @property
    def label(self) -> str:
        return 'JSON'

    def load(self, dump: str) -> Dump:
        try:
            return cast(Dump, json.loads(dump))
        except json.JSONDecodeError as e:
            raise FormatError(self.localizer._('Invalid JSON: {error}.').format(error=e))

    def dump(self, dump: VoidableDump[Dump]) -> str:
        return json.dumps(dump)


class Yaml(Format):
    @property
    def extensions(self) -> set[str]:
        return {'yaml', 'yml'}

    @property
    def label(self) -> str:
        return 'YAML'

    def load(self, dump: str) -> Dump:
        try:
            return cast(Dump, yaml.safe_load(dump))
        except yaml.YAMLError as e:
            raise FormatError(self.localizer._('Invalid YAML: {error}.').format(error=e))

    def dump(self, dump: VoidableDump[Dump]) -> str:
        return yaml.safe_dump(dump)


class FormatRepository(Localizable):
    def __init__(
        self,
        *,
        localizer: Localizer | None = None,
    ):
        super().__init__(localizer=localizer)
        self._formats = (
            Json(localizer=localizer),
            Yaml(localizer=localizer),
        )

    @property
    def formats(self) -> tuple[Format, ...]:
        return self._formats

    @property
    def extensions(self) -> tuple[str, ...]:
        return tuple(
            extension
            for _format in self._formats
            for extension in _format.extensions
        )

    def format_for(self, extension: str) -> Format:
        for format in self._formats:
            if extension in format.extensions:
                return format
        supported_formats = ', '.join([
            f'.{extension} ({format.label})'
            for extension in format.extensions
            for format in self.formats
        ])
        raise FormatError(f'Unknown file format ".{extension}". Supported formats are: {supported_formats}.')
