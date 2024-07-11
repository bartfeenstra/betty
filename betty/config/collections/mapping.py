"""
Define and provide key-value mappings of :py:class:`betty.config.Configuration` instances.
"""

from __future__ import annotations

from abc import abstractmethod
from collections import OrderedDict
from typing import (
    Generic,
    Iterable,
    Any,
    Iterator,
    Self,
    TypeAlias,
    TypeVar,
    SupportsIndex,
    Hashable,
)

from typing_extensions import override

from betty.assertion import assert_sequence, assert_dict
from betty.config import Configuration
from betty.config.collections import ConfigurationCollection
from betty.serde.dump import Dump, VoidableDump, minimize
from betty.typing import Void

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
ConfigurationKey: TypeAlias = SupportsIndex | Hashable | type[Any]
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
        self._configurations: OrderedDict[_ConfigurationKeyT, _ConfigurationT] = (
            OrderedDict()
        )
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
    def replace(self, *values: _ConfigurationT) -> None:
        self_keys = list(self.keys())
        other = {self._get_key(value): value for value in values}
        other_values = list(values)
        other_keys = list(map(self._get_key, other_values))

        # Update items that are kept.
        for key in self_keys:
            if key in other_keys:
                self[key].update(other[key])

        # Add items that are new.
        self.append(*(other[key] for key in other_keys if key not in self_keys))

        # Remove items that should no longer be present.
        self.remove(*(key for key in self_keys if key not in other_keys))

        # Ensure everything is in the correct order.
        self.move_to_beginning(*other_keys)

    @override
    def load(self, dump: Dump) -> None:
        self.clear()
        self.replace(
            *assert_sequence(self.load_item)(
                [
                    self._load_key(item_value_dump, item_key_dump)
                    for item_key_dump, item_value_dump in assert_dict()(dump).items()
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
        for configuration in configurations:
            configuration_key = self._get_key(configuration)
            self._configurations[configuration_key] = configuration
        self.move_to_beginning(*map(self._get_key, configurations))

    @override
    def append(self, *configurations: _ConfigurationT) -> None:
        for configuration in configurations:
            configuration_key = self._get_key(configuration)
            self._configurations[configuration_key] = configuration
        self.move_to_end(*map(self._get_key, configurations))

    @override
    def insert(self, index: int, *configurations: _ConfigurationT) -> None:
        current_configuration_keys = list(self.keys())
        self.append(*configurations)
        self.move_to_end(
            *current_configuration_keys[0:index],
            *map(self._get_key, configurations),
            *current_configuration_keys[index:],
        )

    @override
    def move_to_beginning(self, *configuration_keys: _ConfigurationKeyT) -> None:
        for configuration_key in reversed(configuration_keys):
            self._configurations.move_to_end(configuration_key, False)

    @override
    def move_towards_beginning(self, *configuration_keys: _ConfigurationKeyT) -> None:
        self._move_by_offset(-1, *configuration_keys)

    @override
    def move_to_end(self, *configuration_keys: _ConfigurationKeyT) -> None:
        for configuration_key in configuration_keys:
            self._configurations.move_to_end(configuration_key)

    @override
    def move_towards_end(self, *configuration_keys: _ConfigurationKeyT) -> None:
        self._move_by_offset(1, *configuration_keys)

    def _move_by_offset(
        self, offset: int, *configuration_keys: _ConfigurationKeyT
    ) -> None:
        current_configuration_keys = list(self.keys())
        indices = list(self.to_indices(*configuration_keys))
        if offset > 0:
            indices.reverse()
        for index in indices:
            self.insert(
                index + offset,
                self._configurations.pop(current_configuration_keys[index]),
            )

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
