"""
Define and provide collections of :py:class:`betty.config.Configuration` instances.
"""

from __future__ import annotations

from abc import abstractmethod
from reprlib import recursive_repr
from typing import (
    Generic,
    MutableSequence,
    MutableMapping,
    Iterable,
    Iterator,
    Any,
    TypeAlias,
    TypeVar,
    SupportsIndex,
    Hashable,
    TYPE_CHECKING,
)

from typing_extensions import override

from betty.classtools import repr_instance
from betty.config import Configuration
from betty.functools import slice_to_range

if TYPE_CHECKING:
    from betty.serde.dump import Dump


_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
ConfigurationKey: TypeAlias = SupportsIndex | Hashable | type[Any]
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)


class ConfigurationCollection(
    Configuration, Generic[_ConfigurationKeyT, _ConfigurationT]
):
    """
    Any collection of :py:class:`betty.config.Configuration` values.
    """

    _configurations: (
        MutableSequence[_ConfigurationT]
        | MutableMapping[_ConfigurationKeyT, _ConfigurationT]
    )

    def __init__(
        self,
        configurations: Iterable[_ConfigurationT] | None = None,
    ):
        super().__init__()
        if configurations is not None:
            self.append(*configurations)

    @abstractmethod
    def __iter__(self) -> Iterator[_ConfigurationKeyT] | Iterator[_ConfigurationT]:
        pass

    def __contains__(self, item: Any) -> bool:
        return item in self._configurations

    @abstractmethod
    def __getitem__(self, configuration_key: _ConfigurationKeyT) -> _ConfigurationT:
        pass

    def __delitem__(self, configuration_key: _ConfigurationKeyT) -> None:
        self.remove(configuration_key)

    def __len__(self) -> int:
        return len(self._configurations)

    @override  # type: ignore[callable-functiontype]
    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, configurations=list(self.values()))

    @abstractmethod
    def replace(self, *values: _ConfigurationT) -> None:
        """
        Replace any existing values with the given ones.
        """
        pass

    def remove(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Remove the given keys from the collection.
        """
        for configuration_key in configuration_keys:
            configuration = self._configurations[configuration_key]  # type: ignore[call-overload]
            del self._configurations[configuration_key]  # type: ignore[call-overload]
            self._on_remove(configuration)

    def clear(self) -> None:
        """
        Clear all items from the collection.
        """
        self.remove(*self.keys())

    def _on_add(self, configuration: _ConfigurationT) -> None:
        pass

    def _on_remove(self, configuration: _ConfigurationT) -> None:
        pass

    @abstractmethod
    def to_index(self, configuration_key: _ConfigurationKeyT) -> int:
        """
        Get the index for the given key.
        """
        pass

    def to_indices(self, *configuration_keys: _ConfigurationKeyT) -> Iterator[int]:
        """
        Get the indices for the given keys.
        """
        for configuration_key in configuration_keys:
            yield self.to_index(configuration_key)

    @abstractmethod
    def to_key(self, index: int) -> _ConfigurationKeyT:
        """
        Get the key for the item at the given index.
        """
        pass

    def to_keys(self, *indices: int | slice) -> Iterator[_ConfigurationKeyT]:
        """
        Get the keys for the items at the given indices.
        """
        unique_indices = set()
        for index in indices:
            if isinstance(index, slice):
                for slice_index in slice_to_range(index, self._configurations):
                    unique_indices.add(slice_index)
            else:
                unique_indices.add(index)
        for index in sorted(unique_indices):
            yield self.to_key(index)

    @abstractmethod
    def load_item(self, dump: Dump) -> _ConfigurationT:
        """
        Create and load a new item from the given dump, or raise an assertion error.

        :raise betty.assertion.error.AssertionFailed: Raised when the dump is invalid and cannot be loaded.
        """
        pass

    @abstractmethod
    def keys(self) -> Iterator[_ConfigurationKeyT]:
        """
        Get all keys in this collection.
        """
        pass

    @abstractmethod
    def values(self) -> Iterator[_ConfigurationT]:
        """
        Get all values in this collection.
        """
        pass

    @abstractmethod
    def prepend(self, *configurations: _ConfigurationT) -> None:
        """
        Prepend the given values to the beginning of the sequence.
        """
        pass

    @abstractmethod
    def append(self, *configurations: _ConfigurationT) -> None:
        """
        Append the given values to the end of the sequence.
        """
        pass

    @abstractmethod
    def insert(self, index: int, *configurations: _ConfigurationT) -> None:
        """
        Insert the given values at the given index.
        """
        pass

    @abstractmethod
    def move_to_beginning(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Move the given keys (and their values) to the beginning of the sequence.
        """
        pass

    @abstractmethod
    def move_towards_beginning(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Move the given keys (and their values) one place towards the beginning of the sequence.
        """
        pass

    @abstractmethod
    def move_to_end(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Move the given keys (and their values) to the end of the sequence.
        """
        pass

    @abstractmethod
    def move_towards_end(self, *configuration_keys: _ConfigurationKeyT) -> None:
        """
        Move the given keys (and their values) one place towards the end of the sequence.
        """
        pass
