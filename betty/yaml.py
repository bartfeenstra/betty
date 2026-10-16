"""
YAML support.
"""

from __future__ import annotations

import builtins
import sys
from typing import Final

# YAML data type definitions are based on https://yaml.org/spec/1.1 and https://pyyaml.org/wiki/PyYAMLDocumentation.
# At the time of writing, these definitions are merely a subset of the full YAML spec.
_yaml_mapping_types = (dict,)
if sys.version_info >= (3, 15):
    _yaml_mapping_types = (*_yaml_mapping_types, builtins.frozendict)
yaml_mapping_types: Final[tuple[type, ...]] = _yaml_mapping_types
yaml_sequence_types: Final[tuple[type, ...]] = (list, tuple)
type YamlScalar = None | bool | int | float | str
type _CommonYamlArray[ValueT] = list[ValueT]
type _LoadableYamlArray[ValueT] = _CommonYamlArray[ValueT]
type _DumpableYamlArray[ValueT] = _CommonYamlArray[ValueT] | tuple[ValueT, ...]
type YamlArray[ValueT: YamlData = YamlData] = (
    _LoadableYamlArray[ValueT] | _DumpableYamlArray[ValueT]
)
type _CommonYamlObject[KeyT, ValueT] = dict[KeyT, ValueT]
type _LoadableYamlObject[KeyT, ValueT] = _CommonYamlObject[KeyT, ValueT]
if sys.version_info >= (3, 15):
    type _DumpableYamlObject[KeyT, ValueT] = (
        _CommonYamlObject[KeyT, ValueT] | builtins.frozendict[KeyT, ValueT]
    )
else:
    type _DumpableYamlObject[KeyT, ValueT] = _CommonYamlObject[KeyT, ValueT]
type YamlObject[KeyT: YamlData = YamlData, ValueT: YamlData = YamlData] = (
    _LoadableYamlObject[KeyT, ValueT] | _DumpableYamlObject[KeyT, ValueT]
)
type LoadableYamlData = (
    YamlScalar | _LoadableYamlArray[YamlData] | _LoadableYamlObject[YamlData, YamlData]
)
type DumpableYamlData = (
    YamlScalar | _DumpableYamlArray[YamlData] | _DumpableYamlObject[YamlData, YamlData]
)
type YamlData = LoadableYamlData | DumpableYamlData
