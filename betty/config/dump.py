from __future__ import annotations

from typing import Union, TypeVar, Mapping, Sequence, Type, Dict, List, overload, Literal

from betty.typing import Void

try:
    from typing_extensions import TypeAlias
except ModuleNotFoundError:
    from typing import TypeAlias  # type: ignore


T = TypeVar('T')
U = TypeVar('U')


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


DumpedConfiguration: TypeAlias = Union[
    bool,
    int,
    float,
    str,
    None,
    Sequence['DumpedConfiguration'],
    Mapping[str, 'DumpedConfiguration'],
]
DumpedConfigurationT = TypeVar('DumpedConfigurationT', bound=DumpedConfiguration)
DumpedConfigurationU = TypeVar('DumpedConfigurationU', bound=DumpedConfiguration)


VoidableDumpedConfiguration: TypeAlias = Union[
    DumpedConfiguration,
    bool,
    int,
    float,
    str,
    None,
    Sequence['DumpedConfiguration'],
    Mapping[str, 'DumpedConfiguration'],
    Type[Void],
]
VoidableDumpedConfigurationT = TypeVar('VoidableDumpedConfigurationT', bound=VoidableDumpedConfiguration)
VoidableDumpedConfigurationU = TypeVar('VoidableDumpedConfigurationU', bound=VoidableDumpedConfiguration)


_DumpedConfigurationList: TypeAlias = List[DumpedConfigurationT]


_DumpedConfigurationDict: TypeAlias = Dict[str, DumpedConfigurationT]


_VoidableDumpedConfigurationList: TypeAlias = List[VoidableDumpedConfigurationT]


_VoidableDumpedConfigurationDict: TypeAlias = Dict[str, VoidableDumpedConfigurationT]


_MinimizableDumpedConfiguration: TypeAlias = Union[VoidableDumpedConfiguration, _VoidableDumpedConfigurationList, _VoidableDumpedConfigurationDict]


@overload
def minimize(dumped_configuration: _MinimizableDumpedConfiguration, voidable: Literal[True] = True) -> VoidableDumpedConfiguration:
    pass


@overload
def minimize(dumped_configuration: _MinimizableDumpedConfiguration, voidable: Literal[False]) -> DumpedConfiguration:
    pass


def minimize(dumped_configuration: _MinimizableDumpedConfiguration, voidable: bool = True) -> VoidableDumpedConfiguration:
    if isinstance(dumped_configuration, (Sequence, Mapping)) and not isinstance(dumped_configuration, str):
        if isinstance(dumped_configuration, Sequence):
            dumped_configuration = [
                value
                for value
                in dumped_configuration
                if value is not Void
            ]
            for key in reversed(range(len(dumped_configuration))):
                if dumped_configuration[key] is Void:
                    del dumped_configuration[key]
        if isinstance(dumped_configuration, Mapping):
            dumped_configuration = {
                key: value
                for key, value
                in dumped_configuration.items()
                if value is not Void
            }
        if len(dumped_configuration) or not voidable:
            return dumped_configuration  # type: ignore[return-value]
        return Void
    return dumped_configuration


def void_none(value: VoidableDumpedConfiguration) -> VoidableDumpedConfiguration:
    return Void if value is None else value
