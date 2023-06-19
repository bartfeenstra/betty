from __future__ import annotations

from typing import TypeVar, Generic, Sequence, Mapping, SupportsIndex, Hashable

from typing_extensions import TypeAlias

Dump: TypeAlias = 'bool | int | float | str | None | Sequence[Dump] | Mapping[str, Dump]'
DumpT = TypeVar('DumpT', bound=Dump)
ListDump: TypeAlias = list[DumpT]
DictDump: TypeAlias = dict[str, DumpT]


class Configuration(Generic[DumpT]):
    pass


ConfigurationT = TypeVar('ConfigurationT', bound='Configuration[DumpT]')
ConfigurationKey: TypeAlias = 'SupportsIndex | Hashable | type[object]'
ConfigurationKeyT = TypeVar('ConfigurationKeyT', bound=ConfigurationKey)
ConfigurationCollectionItemDumpT = TypeVar('ConfigurationCollectionItemDumpT', bound=Dump)


class ConfigurationCollection(
    Generic[ConfigurationKeyT, ConfigurationT, DumpT],
    Configuration[DumpT]
):
    pass


# error: If Generic[...] or Protocol[...] is present it should list all type variables  [misc]
class ConfigurationSequence(
    Generic[ConfigurationT, ConfigurationCollectionItemDumpT],
    ConfigurationCollection[
        int,
        ConfigurationT,
        ListDump[ConfigurationCollectionItemDumpT]
    ]
):
    pass


# error: If Generic[...] or Protocol[...] is present it should list all type variables  [misc]
class ConfigurationMapping(
    Generic[ConfigurationKeyT, ConfigurationT, ConfigurationCollectionItemDumpT],
    ConfigurationCollection[
        ConfigurationKeyT,
        ConfigurationT,
        DictDump[ConfigurationCollectionItemDumpT]
    ]
):
    pass


reveal_type(ConfigurationCollection)
# note: Revealed type is "def [ConfigurationKeyT: typing.SupportsIndex | typing.Hashable | type[object], ConfigurationT: betty.test.Configuration[DumpT?], DumpT: bool | int | float | str | None | typing.Sequence[bool | int | float | str | None | typing.Sequence[...] | typing.Mapping[str, ...]] | typing.Mapping[str, bool | int | float | str | None | typing.Sequence[...] | typing.Mapping[str, ...]]] () -> betty.test.ConfigurationCollection[ConfigurationKeyT, ConfigurationT, DumpT]"
reveal_type(ConfigurationSequence)
# note: Revealed type is "def [ConfigurationT: betty.test.Configuration[DumpT?], ConfigurationCollectionItemDumpT: bool | int | float | str | None | typing.Sequence[bool | int | float | str | None | typing.Sequence[...] | typing.Mapping[str, ...]] | typing.Mapping[str, bool | int | float | str | None | typing.Sequence[...] | typing.Mapping[str, ...]], DumpT: bool | int | float | str | None | typing.Sequence[bool | int | float | str | None | typing.Sequence[...] | typing.Mapping[str, ...]] | typing.Mapping[str, bool | int | float | str | None | typing.Sequence[...] | typing.Mapping[str, ...]]] () -> betty.test.ConfigurationSequence[ConfigurationT, ConfigurationCollectionItemDumpT, DumpT]"                                                                           betty/test.py:52:13: note: Revealed type is "def [ConfigurationKeyT: typing.SupportsIndex | typing.Hashable | type[object], ConfigurationT: betty.test.Configuration[DumpT?], ConfigurationCollectionItemDumpT: bool | int | float | str | None | typing.Sequence[bool | int | float | str | None | typing.Sequence[...] | typing.Mapping[str, ...]] | typing.Mapping[str, bool | int | float | str | None | typing.Sequence[...] | typing.Mapping[str, ...]], DumpT: bool | int | float | str | None | typing.Sequence[bool | int | float | str | None | typing.Sequence[...] | typing.Mapping[str, ...]] | typing.Mapping[str, bool | int | float | str | None | typing.Sequence[...] | typing.Mapping[str, ...]]] () -> betty.test.ConfigurationMapping[ConfigurationKeyT, ConfigurationT, ConfigurationCollectionItemDumpT, DumpT]"
reveal_type(ConfigurationMapping)
# note: Revealed type is "def [ConfigurationKeyT: typing.SupportsIndex | typing.Hashable | type[object], ConfigurationT: betty.test.Configuration[DumpT?], ConfigurationCollectionItemDumpT: bool | int | float | str | None | typing.Sequence[bool | int | float | str | None | typing.Sequence[...] | typing.Mapping[str, ...]] | typing.Mapping[str, bool | int | float | str | None | typing.Sequence[...] | typing.Mapping[str, ...]], DumpT: bool | int | float | str | None | typing.Sequence[bool | int | float | str | None | typing.Sequence[...] | typing.Mapping[str, ...]] | typing.Mapping[str, bool | int | float | str | None | typing.Sequence[...] | typing.Mapping[str, ...]]] () -> betty.test.ConfigurationMapping[ConfigurationKeyT, ConfigurationT, ConfigurationCollectionItemDumpT, DumpT]"


class DummyConfiguration(Configuration[bool]):
    pass


# error: "ConfigurationMapping" expects 4 type arguments, but 3 given  [type-arg]
class DummyConfigurationMapping(ConfigurationMapping[str, DummyConfiguration, bool]):
    pass


# @todo Add a little something so the tests fail, and I remember to remove this file.
[] == {}
