"""
Define and provide sequences of :py:class:`betty.config.Configuration` instances.
"""

from __future__ import annotations

from typing import (
    Generic,
    Iterable,
    MutableSequence,
    Any,
    overload,
    Sequence,
    Iterator,
    Self,
    TypeVar,
)

from typing_extensions import override

from betty.assertion import assert_sequence
from betty.config import Configuration
from betty.config.collections import ConfigurationCollection
from betty.serde.dump import Dump, VoidableDump, minimize

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class ConfigurationSequence(
    ConfigurationCollection[int, _ConfigurationT], Generic[_ConfigurationT]
):
    """
    A sequence of configuration values.
    """

    def __init__(
        self,
        configurations: Iterable[_ConfigurationT] | None = None,
    ):
        self._configurations: MutableSequence[_ConfigurationT] = []
        super().__init__(configurations)

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return list(self.values()) == list(other.values())

    @override
    def to_index(self, configuration_key: int) -> int:
        return configuration_key

    @override
    def to_key(self, index: int) -> int:
        return index

    @override
    @overload
    def __getitem__(self, configuration_key: int) -> _ConfigurationT:
        pass

    @override
    @overload
    def __getitem__(self, configuration_key: slice) -> Sequence[_ConfigurationT]:
        pass

    @override
    def __getitem__(
        self, configuration_key: int | slice
    ) -> _ConfigurationT | Sequence[_ConfigurationT]:
        return self._configurations[configuration_key]

    @override
    def __iter__(self) -> Iterator[_ConfigurationT]:
        return (configuration for configuration in self._configurations)

    @override
    def keys(self) -> Iterator[int]:
        return iter(range(0, len(self._configurations)))

    @override
    def values(self) -> Iterator[_ConfigurationT]:
        yield from self._configurations

    @override
    def update(self, other: Self) -> None:
        self.clear()
        self.append(*other)

    @override
    def replace(self, *configurations: _ConfigurationT) -> None:
        self.clear()
        self.append(*configurations)

    @override
    def load(self, dump: Dump) -> None:
        self.replace(*assert_sequence(self.load_item)(dump))

    @override
    def dump(self) -> VoidableDump:
        return minimize(
            [configuration.dump() for configuration in self._configurations]
        )

    @override
    def prepend(self, *configurations: _ConfigurationT) -> None:
        for configuration in configurations:
            self._pre_add(configuration)
            self._configurations.insert(0, configuration)

    @override
    def append(self, *configurations: _ConfigurationT) -> None:
        for configuration in configurations:
            self._pre_add(configuration)
            self._configurations.append(configuration)

    @override
    def insert(self, index: int, *configurations: _ConfigurationT) -> None:
        for configuration in reversed(configurations):
            self._pre_add(configuration)
            self._configurations.insert(index, configuration)

    @override
    def move_to_beginning(self, *configuration_keys: int) -> None:
        self.move_to_end(
            *configuration_keys,
            *[
                index
                for index in range(0, len(self._configurations))
                if index not in configuration_keys
            ],
        )

    @override
    def move_towards_beginning(self, *configuration_keys: int) -> None:
        for index in configuration_keys:
            self._configurations.insert(index - 1, self._configurations.pop(index))

    @override
    def move_to_end(self, *configuration_keys: int) -> None:
        for index in configuration_keys:
            self._configurations.append(self._configurations[index])
        for index in reversed(configuration_keys):
            self._configurations.pop(index)

    @override
    def move_towards_end(self, *configuration_keys: int) -> None:
        for index in reversed(configuration_keys):
            self._configurations.insert(index + 1, self._configurations.pop(index))
