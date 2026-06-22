"""
Test utilities for :py:mod:`betty.store`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.store import StoreItem, TransientStore

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from contextlib import AbstractAsyncContextManager


def _scopes() -> pytest.MarkDecorator:
    return pytest.mark.parametrize(
        "scopes",
        [
            (),
            ("scopey", "dopey"),
        ],
    )


class StoreTestBase[ItemValueT]:
    """
    A base class for tests of :py:class:`betty.store.Store` implementations.
    """

    def _new_sut(
        self, *, scopes: Sequence[str] = ()
    ) -> AbstractAsyncContextManager[TransientStore[ItemValueT]]:
        raise NotImplementedError

    def _values(self) -> Iterator[ItemValueT]:
        raise NotImplementedError

    async def test_with_scope(self) -> None:
        """
        Test implementations of :py:meth:`betty.store.Store.with_scope`.
        """
        for value in self._values():
            async with self._new_sut() as sut:
                sut_with_scope_one = sut.with_scope("scopey")
                sut_with_scope_two = sut.with_scope("scopey")
                assert sut_with_scope_one is not sut
                assert sut_with_scope_two is not sut
                key = "hello-world"
                await sut_with_scope_one.set(key, value)
                item = await sut_with_scope_two.get(key)
                assert item
                assert await item.value() == value

    @_scopes()
    async def test_has__without_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.store.Store.has`.
        """
        async with self._new_sut(scopes=scopes) as sut:
            assert not await sut.get("id")

    @_scopes()
    async def test_has__with_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.store.Store.has`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set("id", value)
                assert await sut.has("id")

    @_scopes()
    async def test_hasset__without_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.store.Store.hasset`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                async with sut.hasset("id") as result:
                    assert result is not None
                    await result(value)
                item = await sut.get("id")
                assert item is not None
                assert await item.value() == value

    @_scopes()
    async def test_hasset__with_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.store.Store.hasset`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set("id", value)
                async with sut.hasset("id") as result:
                    assert result is None

    @_scopes()
    async def test_get__without_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.store.Store.get`.
        """
        async with self._new_sut(scopes=scopes) as sut:
            item = await sut.get("id")
            assert item is None

    @_scopes()
    async def test_set__and_get(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.store.Store.get` and :py:meth:`betty.store.Store.set`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set("id", value)
                item = await sut.get("id")
                assert item is not None
                assert await item.value() == value

    @_scopes()
    async def test_set__and_get_with_modified(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.store.Store.get` and :py:meth:`betty.store.Store.set`.
        """
        modified = 123456789
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set("id", value, modified=modified)
                item = await sut.get("id")
                assert item is not None
                assert item.modified == modified

    @_scopes()
    async def test_getset__without_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.store.Store.getset`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                async with sut.getset("id") as result:
                    assert not isinstance(result, StoreItem)
                    await result(value)
                item = await sut.get("id")
                assert item is not None
                assert await item.value() == value

    @_scopes()
    async def test_getset__with_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.store.Store.getset`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set("id", value)
                async with sut.getset("id") as result:
                    assert isinstance(result, StoreItem)
                    assert await result.value() == value


class TransientStoreTestBase[ItemValueT](StoreTestBase[ItemValueT]):
    """
    A base class for tests of :py:class:`betty.store.TransientStore` implementations.
    """

    @_scopes()
    async def test_clear(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.store.TransientStore.clear`.
        """
        async with self._new_sut(scopes=scopes) as sut:
            await sut.set("id", next(self._values()))
            await sut.clear()
            assert await sut.get("id") is None

    @_scopes()
    async def test_delete(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.store.TransientStore.delete`.
        """
        async with self._new_sut(scopes=scopes) as sut:
            await sut.set("id", next(self._values()))
            await sut.delete("id")
            assert await sut.get("id") is None
