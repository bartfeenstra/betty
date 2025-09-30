"""
Provide serialization formats.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast, final

import yaml
from typing_extensions import override

from betty.locale.localizable import Plain, _
from betty.serde.dump import Dump
from betty.serde.format import Format, FormatDefinition, FormatError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.typing import Voidable


@final
@FormatDefinition(
    id="json",
    label=Plain("JSON"),
)
class Json(Format):
    """
    Defines the `JSON <https://json.org/>`_ (de)serialization format.
    """

    @override
    @classmethod
    def extensions(cls) -> Sequence[str]:
        return [".json"]

    @override
    def load(self, dump: str) -> Dump:
        try:
            return cast(Dump, json.loads(dump))
        except json.JSONDecodeError as e:
            raise FormatError(
                _("Invalid JSON: {error}.").format(error=str(e))
            ) from None

    @override
    def dump(self, dump: Voidable[Dump]) -> str:
        return json.dumps(dump)


@final
@FormatDefinition(
    id="yaml",
    label=Plain("YAML"),
)
class Yaml(Format):
    """
    Defines the `YAML <https://yaml.org/>`_ (de)serialization format.
    """

    @override
    @classmethod
    def extensions(cls) -> Sequence[str]:
        return [".yaml", ".yml"]

    @override
    def load(self, dump: str) -> Dump:
        try:
            return cast(Dump, yaml.safe_load(dump))
        except yaml.YAMLError as e:
            raise FormatError(
                _("Invalid YAML: {error}.").format(error=str(e))
            ) from None

    @override
    def dump(self, dump: Voidable[Dump]) -> str:
        return yaml.safe_dump(dump)
