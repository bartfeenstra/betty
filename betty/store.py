"""
The key-value store API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager


class StoreItem[ItemValueT](ABC):
    """
    A store item.
    """

    @property
    @abstractmethod
    def modified(self) -> int | float:
        """
        Get the time this item was last modified, in seconds.
        """

    @abstractmethod
    async def value(self) -> ItemValueT:
        """
        Get this item's value.
        """


type StoreItemValueSetter[_ItemValueT] = Callable[[_ItemValueT], Awaitable[None]]


class Store[ItemValueT](ABC):
    """
    A key-value store.

    To test your own subclasses, use :py:class:`betty.test_utils.store.StoreTestBase`.
    """

    @abstractmethod
    def with_scope(self, scope: str, /) -> Self:
        """
        Return a new nested store with the given scope.
        """

    async def has(self, key: str, /) -> bool:
        """
        Check if an item with the given key exists.
        """
        return await self.get(key) is not None

    @abstractmethod
    def hasset(
        self, key: str, /
    ) -> AbstractAsyncContextManager[StoreItemValueSetter[ItemValueT] | None]:
        """
        Check if an item with the given key exists, and if not, provide a setter to add or update it within the same atomic operation.
        """

    @abstractmethod
    async def get(self, key: str, /) -> StoreItem[ItemValueT] | None:
        """
        Get the item with the given key.
        """

    @abstractmethod
    async def set(
        self,
        key: str,
        value: ItemValueT,
        *,
        modified: float | None = None,
    ) -> None:
        """
        Add or update an item.
        """

    @abstractmethod
    def getset(
        self, key: str, /
    ) -> AbstractAsyncContextManager[
        StoreItemValueSetter[ItemValueT] | StoreItem[ItemValueT]
    ]:
        """
        Get the item with the given key, or provide a setter to add it within the same atomic operation.
        """


class TransientStore[ItemValueT](Store[ItemValueT]):
    """
    A key-value store whose items are transient, meaning that may be deleted, and are not guaranteed to persist.
    """

    @abstractmethod
    async def clear(self) -> None:
        """
        Clear all items from the store.

        This operation s unsafe and MAY cause other concurrent operations on this store to fail.
        """

    @abstractmethod
    async def delete(self, key: str, /) -> None:
        """
        Delete the item with the given key.

        This operation s unsafe and MAY cause other concurrent operations on this store to fail.
        """
