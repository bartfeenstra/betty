"""
Define and provide collections of :py:class:`betty.config.Configuration` instances.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import (
    Hashable,
    Iterable,
    Iterator,
    MutableMapping,
    MutableSequence,
)
from typing import TYPE_CHECKING, Any, Generic, SupportsIndex, TypeAlias

from typing_extensions import TypeVar, override

from betty.config import Configuration

if TYPE_CHECKING:
    from betty.serde.dump import Dump

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
ConfigurationKey: TypeAlias = SupportsIndex | Hashable | type[Any]
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)
_ResolvableConfigurationKeyT = TypeVar("_ResolvableConfigurationKeyT")


class ConfigurationCollection(
    Configuration,
    Generic[_ConfigurationKeyT, _ResolvableConfigurationKeyT, _ConfigurationT],
):
    """
    Any collection of :py:class:`betty.config.Configuration` values.

    To test your own subclasses, use :py:class:`betty.test_utils.config.collections.ConfigurationCollectionTestBase`.
    """

    _configurations: (
        MutableSequence[_ConfigurationT]
        | MutableMapping[_ConfigurationKeyT, _ConfigurationT]
    )

    def __init__(self, configurations: Iterable[_ConfigurationT] | None = None, /):
        super().__init__()
        if configurations is not None:
            self.append(*configurations)

    @abstractmethod
    def _resolve_key(
        self, configuration_key: _ConfigurationKeyT | _ResolvableConfigurationKeyT, /
    ) -> _ConfigurationKeyT:
        """
        Resolve a configuration key.
        """

    @abstractmethod
    def __iter__(
        self,
    ) -> Iterator[_ConfigurationKeyT] | Iterator[_ConfigurationT]:
        pass

    @abstractmethod
    def __getitem__(
        self, configuration_key: _ConfigurationKeyT | _ResolvableConfigurationKeyT
    ) -> _ConfigurationT:
        pass

    def __delitem__(
        self, configuration_key: _ConfigurationKeyT | _ResolvableConfigurationKeyT
    ) -> None:
        self.remove(configuration_key)

    def __len__(self) -> int:
        return len(self._configurations)

    @abstractmethod
    def replace(self, *configurations: _ConfigurationT) -> None:
        """
        Replace any existing values with the given ones.
        """

    def remove(
        self, *configuration_keys: _ConfigurationKeyT | _ResolvableConfigurationKeyT
    ) -> None:
        """
        Remove the given keys from the collection.
        """
        self.assert_mutable()
        for configuration_key in configuration_keys:
            configuration_key = self._resolve_key(configuration_key)
            configuration_key = self._resolve_key(configuration_key)
            try:
                configuration = self._configurations[configuration_key]  # type: ignore[call-overload]
            except LookupError:
                continue
            else:
                del self._configurations[configuration_key]  # type: ignore[call-overload]
                self._post_remove(configuration)

    def clear(self) -> None:
        """
        Clear all items from the collection.
        """
        self.remove(*self.keys())

    def _pre_add(self, configuration: _ConfigurationT, /) -> None:
        pass

    def _post_remove(self, configuration: _ConfigurationT, /) -> None:
        pass

    @classmethod
    @abstractmethod
    def _load_item(cls, dump: Dump, /) -> _ConfigurationT:
        """
        Create and load a new item from the given dump, or raise an assertion error.

        :raise betty.exception.HumanFacingException: Raised when the dump is invalid and cannot be loaded.
        """

    @abstractmethod
    def keys(self) -> Iterator[_ConfigurationKeyT]:
        """
        Get all keys in this collection.
        """

    @abstractmethod
    def values(self) -> Iterator[_ConfigurationT]:
        """
        Get all values in this collection.
        """

    @abstractmethod
    def prepend(self, *configurations: _ConfigurationT) -> None:
        """
        Prepend the given values to the beginning of the sequence.
        """

    @abstractmethod
    def append(self, *configurations: _ConfigurationT) -> None:
        """
        Append the given values to the end of the sequence.
        """

    @abstractmethod
    def insert(self, index: int, *configurations: _ConfigurationT) -> None:
        """
        Insert the given values at the given index.
        """

    @override
    def get_mutables(self) -> Iterable[object]:
        return self.values()
