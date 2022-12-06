from __future__ import annotations

from typing import Union, TypeVar, Mapping, Sequence, Type, Any

from betty.typing import Void

try:
    from typing_extensions import TypeAlias
except ModuleNotFoundError:
    from typing import TypeAlias  # type: ignore


DumpedConfigurationType: TypeAlias = Union[
    bool,
    int,
    float,
    str,
    None,
    list,
    dict,
]
DumpedConfigurationTypeT = TypeVar('DumpedConfigurationTypeT', bound=DumpedConfigurationType)


DumpedConfigurationImport: TypeAlias = Union[
    bool,
    int,
    float,
    str,
    None,
    Sequence['DumpedConfigurationImport'],
    Mapping[str, 'DumpedConfigurationImport'],
]
DumpedConfigurationImportT = TypeVar('DumpedConfigurationImportT', bound=DumpedConfigurationImport)
DumpedConfigurationImportU = TypeVar('DumpedConfigurationImportU', bound=DumpedConfigurationImport)


DumpedConfigurationExport: TypeAlias = Union[
    bool,
    int,
    float,
    str,
    None,
    Sequence['DumpedConfigurationExport'],
    Mapping[str, 'DumpedConfigurationExport'],
    Type[Void],
]
DumpedConfigurationExportT = TypeVar('DumpedConfigurationExportT', bound=DumpedConfigurationExport)
DumpedConfigurationExportU = TypeVar('DumpedConfigurationExportU', bound=DumpedConfigurationExport)


DumpedConfiguration: TypeAlias = Union[DumpedConfigurationImport, DumpedConfigurationExport]
DumpedConfigurationT = TypeVar('DumpedConfigurationT', bound=DumpedConfiguration)


DumpedConfigurationList: TypeAlias = Sequence[DumpedConfigurationT]


DumpedConfigurationDict: TypeAlias = Mapping[str, DumpedConfigurationT]


DumpedConfigurationCollection: TypeAlias = Union[DumpedConfigurationList, DumpedConfigurationDict]


def _minimize_collection(dumped_configuration: Any, keys: Any) -> None:
    for key in keys:
        dumped_configuration[key] = minimize(dumped_configuration[key])
        if dumped_configuration[key] is Void:
            del dumped_configuration[key]


def minimize_list(dumped_configuration: DumpedConfigurationList[DumpedConfigurationExportT]) -> Union[DumpedConfigurationList[DumpedConfigurationExportT], Type[Void]]:
    _minimize_collection(dumped_configuration, reversed(range(len(dumped_configuration))))
    if not len(dumped_configuration):
        return Void
    return dumped_configuration


def minimize_dict(dumped_configuration: DumpedConfigurationDict[DumpedConfigurationExportT], void_empty: bool = False) -> Union[DumpedConfigurationDict[DumpedConfigurationExportT], Type[Void]]:
    _minimize_collection(dumped_configuration, list(dumped_configuration.keys()))
    if not void_empty or len(dumped_configuration) > 0:
        return dumped_configuration
    return Void


def minimize(dumped_configuration: DumpedConfigurationExport) -> Union[DumpedConfigurationExport, Type[Void]]:
    if isinstance(dumped_configuration, list):
        return minimize_list(dumped_configuration)
    if isinstance(dumped_configuration, dict):
        return minimize_dict(dumped_configuration)
    return dumped_configuration
