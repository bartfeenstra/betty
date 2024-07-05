"""
Provide serialization formats.
"""

from __future__ import annotations

import json
from typing import cast, Sequence, TYPE_CHECKING

import yaml
from typing_extensions import override

from betty.locale.localizable import plain, Localizable, _
from betty.serde.dump import Dump, VoidableDump
from betty.serde.load import FormatError

if TYPE_CHECKING:
    from betty.locale import Localizer


class Format:
    """
    Defines a (de)serialization format.
    """

    @property
    def extensions(self) -> set[str]:
        """
        The file extensions this format can (de)serialize.

        Extensions MUST NOT include a leading dot.
        """
        raise NotImplementedError(repr(self))

    @property
    def label(self) -> Localizable:
        """
        The format's human-readable label.
        """
        raise NotImplementedError(repr(self))

    def load(self, dump: str) -> Dump:
        """
        Deserialize data.
        """
        raise NotImplementedError(repr(self))

    def dump(self, dump: VoidableDump) -> str:
        """
        Serialize data.
        """
        raise NotImplementedError(repr(self))


class Json(Format):
    """
    Defines the `JSON <https://json.org/>`_ (de)serialization format.
    """

    @override
    @property
    def extensions(self) -> set[str]:
        return {"json"}

    @override
    @property
    def label(self) -> Localizable:
        return plain("JSON")

    @override
    def load(self, dump: str) -> Dump:
        try:
            return cast(Dump, json.loads(dump))
        except json.JSONDecodeError as e:
            raise FormatError(
                _("Invalid JSON: {error}.").format(error=str(e))
            ) from None

    @override
    def dump(self, dump: VoidableDump) -> str:
        return json.dumps(dump)


class Yaml(Format):
    """
    Defines the `YAML <https://yaml.org/>`_ (de)serialization format.
    """

    @override
    @property
    def extensions(self) -> set[str]:
        return {"yaml", "yml"}

    @override
    @property
    def label(self) -> Localizable:
        return plain("YAML")

    @override
    def load(self, dump: str) -> Dump:
        try:
            return cast(Dump, yaml.safe_load(dump))
        except yaml.YAMLError as e:
            raise FormatError(
                _("Invalid YAML: {error}.").format(error=str(e))
            ) from None

    @override
    def dump(self, dump: VoidableDump) -> str:
        return yaml.safe_dump(dump)


class FormatRepository:
    """
    Exposes the available (de)serialization formats.
    """

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
        """
        All formats in this repository.
        """
        return self._serde_formats

    @property
    def extensions(self) -> tuple[str, ...]:
        """
        All file extensions supported by the formats in this repository.
        """
        return tuple(
            extension
            for _format in self._serde_formats
            for extension in _format.extensions
        )

    def format_for(self, extension: str) -> Format:
        """
        Get the (de)serialization format for the given file extension.

        The extension MUST NOT include a leading dot.
        """
        for serde_format in self._serde_formats:
            if extension in serde_format.extensions:
                return serde_format
        raise FormatError(
            _(
                'Unknown file format ".{extension}". Supported formats are: {supported_formats}.'
            ).format(extension=extension, supported_formats=FormatStr(self.formats))
        )


class FormatStr(Localizable):
    """
    Localize and format a sequence of (de)serialization formats.
    """

    def __init__(self, serde_formats: Sequence[Format]):
        self._serde_formats = serde_formats

    @override
    def localize(self, localizer: Localizer) -> str:
        return ", ".join(
            [
                f".{extension} ({serde_format.label.localize(localizer)})"
                for serde_format in self._serde_formats
                for extension in serde_format.extensions
            ]
        )
