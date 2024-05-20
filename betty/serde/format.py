"""
Provide serialization formats.
"""

from __future__ import annotations

import json
from typing import cast, Sequence

import yaml

from betty.locale import Str, Localizer, Localizable
from betty.serde.dump import Dump, VoidableDump
from betty.serde.load import FormatError


class Format:
    @property
    def extensions(self) -> set[str]:
        raise NotImplementedError(repr(self))

    @property
    def label(self) -> Str:
        raise NotImplementedError(repr(self))

    def load(self, dump: str) -> Dump:
        raise NotImplementedError(repr(self))

    def dump(self, dump: VoidableDump) -> str:
        raise NotImplementedError(repr(self))


class Json(Format):
    @property
    def extensions(self) -> set[str]:
        return {"json"}

    @property
    def label(self) -> Str:
        return Str.plain("JSON")

    def load(self, dump: str) -> Dump:
        try:
            return cast(Dump, json.loads(dump))
        except json.JSONDecodeError as e:
            raise FormatError(
                Str._(
                    "Invalid JSON: {error}.",
                    error=str(e),
                )
            ) from None

    def dump(self, dump: VoidableDump) -> str:
        return json.dumps(dump)


class Yaml(Format):
    @property
    def extensions(self) -> set[str]:
        return {"yaml", "yml"}

    @property
    def label(self) -> Str:
        return Str.plain("YAML")

    def load(self, dump: str) -> Dump:
        try:
            return cast(Dump, yaml.safe_load(dump))
        except yaml.YAMLError as e:
            raise FormatError(
                Str._(
                    "Invalid YAML: {error}.",
                    error=str(e),
                )
            ) from None

    def dump(self, dump: VoidableDump) -> str:
        return yaml.safe_dump(dump)


class FormatRepository:
    def __init__(
        self,
    ):
        super().__init__()
        self._serde_formats = (
            Json(),
            Yaml(),
        )

    @property
    def formats(self) -> tuple[Format, ...]:
        return self._serde_formats

    @property
    def extensions(self) -> tuple[str, ...]:
        return tuple(
            extension
            for _format in self._serde_formats
            for extension in _format.extensions
        )

    def format_for(self, extension: str) -> Format:
        for serde_format in self._serde_formats:
            if extension in serde_format.extensions:
                return serde_format
        raise FormatError(
            Str._(
                'Unknown file format ".{extension}". Supported formats are: {supported_formats}.',
                extension=extension,
                supported_formats=FormatStr(self.formats),
            )
        )


class FormatStr(Localizable):
    def __init__(self, serde_formats: Sequence[Format]):
        self._serde_formats = serde_formats

    def localize(self, localizer: Localizer) -> str:
        return ", ".join(
            [
                f".{extension} ({serde_format.label.localize(localizer)})"
                for serde_format in self._serde_formats
                for extension in serde_format.extensions
            ]
        )
