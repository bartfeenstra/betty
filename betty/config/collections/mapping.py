"""
Define and provide key-value mappings of :py:class:`betty.config.Configuration` instances.
"""

from __future__ import annotations

from abc import abstractmethod
from contextlib import suppress
from typing import (
    Generic,
    Iterable,
    Any,
    Iterator,
    Self,
    TypeVar,
)

from typing_extensions import override

from betty.assertion import assert_sequence, assert_mapping
from betty.config import Configuration
from betty.config.collections import ConfigurationCollection, ConfigurationKey
from betty.serde.dump import Dump, VoidableDump, minimize
from betty.typing import Void

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)


class ConfigurationMapping(
    ConfigurationCollection[_ConfigurationKeyT, _ConfigurationT],
    Generic[_ConfigurationKeyT, _ConfigurationT],
):
    """
    A key-value mapping where values are :py:class:`betty.config.Configuration`.
    """

    def __init__(
        self,
        configurations: Iterable[_ConfigurationT] | None = None,
    ):
        self._configurations: dict[_ConfigurationKeyT, _ConfigurationT] = {}
        super().__init__(configurations)

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return {
            self._get_key(configuration): configuration
            for configuration in self.values()
        } == {
            self._get_key(configuration): configuration
            for configuration in other.values()
        }

    def _minimize_item_dump(self) -> bool:
        return False

    @override
    def to_index(self, configuration_key: _ConfigurationKeyT) -> int:
        return list(self._configurations.keys()).index(configuration_key)

    @override
    def to_key(self, index: int) -> _ConfigurationKeyT:
        return list(self._configurations.keys())[index]

    @override
    def __getitem__(self, configuration_key: _ConfigurationKeyT) -> _ConfigurationT:
        return self._configurations[configuration_key]

    @override
    def __iter__(self) -> Iterator[_ConfigurationKeyT]:
        return (configuration_key for configuration_key in self._configurations)

    @override
    def keys(self) -> Iterator[_ConfigurationKeyT]:
        return (configuration_key for configuration_key in self._configurations)

    @override
    def values(self) -> Iterator[_ConfigurationT]:
        yield from self._configurations.values()

    @override
    def update(self, other: Self) -> None:
        self.replace(*other.values())

    @override
    def replace(self, *configurations: _ConfigurationT) -> None:
        self.clear()
        self.append(*configurations)

    @override
    def load(self, dump: Dump) -> None:
        self.clear()
        self.replace(
            *assert_sequence(self.load_item)(
                [
                    self._load_key(item_value_dump, item_key_dump)
                    for item_key_dump, item_value_dump in assert_mapping()(dump).items()
                ]
            )
        )

    @override
    def dump(self) -> VoidableDump:
        dump = {}
        for configuration_item in self._configurations.values():
            item_dump = configuration_item.dump()
            if item_dump is not Void:
                item_dump, configuration_key = self._dump_key(item_dump)
                if self._minimize_item_dump():
                    item_dump = minimize(item_dump)
                dump[configuration_key] = item_dump
        return minimize(dump)

    @override
    def prepend(self, *configurations: _ConfigurationT) -> None:
        self.insert(0, *configurations)

    @override
    def append(self, *configurations: _ConfigurationT) -> None:
        for configuration in configurations:
            configuration_key = self._get_key(configuration)
            with suppress(KeyError):
                del self._configurations[configuration_key]
            self._configurations[configuration_key] = configuration

    @override
    def insert(self, index: int, *configurations: _ConfigurationT) -> None:
        self.remove(*map(self._get_key, configurations))
        existing_configurations = list(self.values())
        self._configurations = {
            self._get_key(configuration): configuration
            for configuration in (
                *existing_configurations[:index],
                *configurations,
                *existing_configurations[index:],
            )
        }

    @abstractmethod
    def _get_key(self, configuration: _ConfigurationT) -> _ConfigurationKeyT:
        pass

    @abstractmethod
    def _load_key(
        self,
        item_dump: Dump,
        key_dump: str,
    ) -> Dump:
        pass

    @abstractmethod
    def _dump_key(self, item_dump: VoidableDump) -> tuple[VoidableDump, str]:
        pass
