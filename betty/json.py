"""
JSON support.
"""

from __future__ import annotations

import builtins
import sys

# JSON data type definitions are based on https://docs.python.org/3/library/json.html#py-to-json-table.
type JsonScalar = None | bool | int | float | str
type _CommonJsonArray[ValueT] = list[ValueT]
type _LoadableJsonArray[ValueT] = _CommonJsonArray[ValueT]
type _DumpableJsonArray[ValueT] = _CommonJsonArray[ValueT] | tuple[ValueT, ...]
type JsonArray[ValueT: JsonData = JsonData] = (
    _LoadableJsonArray[ValueT] | _DumpableJsonArray[ValueT]
)
type _CommonJsonObject[ValueT] = dict[str, ValueT]
type _LoadableJsonObject[ValueT] = _CommonJsonObject[ValueT]
if sys.version_info >= (3, 15):
    type _DumpableJsonObject[ValueT] = (
        _CommonJsonObject[ValueT] | builtins.frozendict[str, ValueT]
    )
else:
    type _DumpableJsonObject[ValueT] = _CommonJsonObject[ValueT]
type JsonObject[ValueT: JsonData = JsonData] = (
    _LoadableJsonObject[ValueT] | _DumpableJsonObject[ValueT]
)
type LoadableJsonData = (
    JsonScalar | _LoadableJsonArray[JsonData] | _LoadableJsonObject[JsonData]
)
type DumpableJsonData = (
    JsonScalar | _DumpableJsonArray[JsonData] | _DumpableJsonObject[JsonData]
)
type JsonData = LoadableJsonData | DumpableJsonData
