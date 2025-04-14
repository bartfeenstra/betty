"""
Provide serialization formats.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast, final

import yaml
from typing_extensions import override

from betty.locale.localizable import _, static
from betty.plugin import ShorthandPluginBase
from betty.serde.dump import Dump
from betty.serde.format import Format, FormatError

if TYPE_CHECKING:
    from betty.typing import Voidable


@final
class Json(ShorthandPluginBase, Format):
    """
    Defines the `JSON <https://json.org/>`_ (de)serialization format.
    """

    _plugin_id = "json"
    _plugin_label = static("JSON")

    @override
    @classmethod
    def extensions(cls) -> set[str]:
        return {".json"}

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
class Yaml(ShorthandPluginBase, Format):
    """
    Defines the `YAML <https://yaml.org/>`_ (de)serialization format.
    """

    _plugin_id = "yaml"
    _plugin_label = static("YAML")

    @override
    @classmethod
    def extensions(cls) -> set[str]:
        return {".yaml", ".yml"}

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
