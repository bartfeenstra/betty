"""
Test utilities for :py:mod:`betty.cache`.
"""

from collections.abc import Iterator, Sequence
from contextlib import AbstractAsyncContextManager
from typing import Generic, TypeVar

import pytest

from betty.cache import Cache, CacheItem

_CacheItemValueT = TypeVar("_CacheItemValueT")


class CacheTestBase(Generic[_CacheItemValueT]):
    """
    A base class for tests of :py:class:`betty.cache.Cache` implementations.
    """

    def _new_sut(
        self,
        *,
        scopes: Sequence[str] | None = None,
    ) -> AbstractAsyncContextManager[Cache[_CacheItemValueT]]:
        raise NotImplementedError

    def _values(self) -> Iterator[_CacheItemValueT]:
        raise NotImplementedError

    @staticmethod
    def _scopes() -> pytest.MarkDecorator:
        return pytest.mark.parametrize(
            "scopes",
            [
                (),
                ("scopey", "dopey"),
            ],
        )

    async def test_with_scope(self) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.with_scope`.
        """
        for value in self._values():
            async with self._new_sut() as sut:
                sut_with_scope_one = sut.with_scope("scopey")
                sut_with_scope_two = sut.with_scope("scopey")
                assert sut_with_scope_one is not sut
                assert sut_with_scope_two is not sut
                cache_item_id = "hello-world"
                await sut_with_scope_one.set(cache_item_id, value)
                cache_item = await sut_with_scope_two.get(cache_item_id)
                assert cache_item
                assert await cache_item.value() == value

    @_scopes()
    async def test_has__without_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.has`.
        """
        async with self._new_sut(scopes=scopes) as sut:
            assert not await sut.get("id")

    @_scopes()
    async def test_has__with_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.has`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set("id", value)
                assert await sut.has("id")

    @_scopes()
    async def test_hasset__without_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.hasset`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                async with sut.hasset("id") as result:
                    assert result is not None
                    await result(value)
                cache_item = await sut.get("id")
                assert cache_item is not None
                assert await cache_item.value() == value

    @_scopes()
    async def test_hasset__with_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.hasset`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set("id", value)
                async with sut.hasset("id") as result:
                    assert result is None

    @_scopes()
    async def test_get__without_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.get`.
        """
        async with self._new_sut(scopes=scopes) as sut:
            cache_item = await sut.get("id")
            assert cache_item is None

    @_scopes()
    async def test_set__and_get(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.get` and :py:meth:`betty.cache.Cache.set`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set("id", value)
                cache_item = await sut.get("id")
                assert cache_item is not None
                assert await cache_item.value() == value

    @_scopes()
    async def test_set__and_get_with_modified(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.get` and :py:meth:`betty.cache.Cache.set`.
        """
        modified = 123456789
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set("id", value, modified=modified)
                cache_item = await sut.get("id")
                assert cache_item is not None
                assert cache_item.modified == modified

    @_scopes()
    async def test_getset__without_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.getset`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                async with sut.getset("id") as result:
                    assert not isinstance(result, CacheItem)
                    await result(value)
                cache_item = await sut.get("id")
                assert cache_item is not None
                assert await cache_item.value() == value

    @_scopes()
    async def test_getset__with_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.getset`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set("id", value)
                async with sut.getset("id") as result:
                    assert isinstance(result, CacheItem)
                    assert await result.value() == value

    @_scopes()
    async def test_delete(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.delete`.
        """
        async with self._new_sut(scopes=scopes) as sut:
            await sut.set("id", next(self._values()))
            await sut.delete("id")
            assert await sut.get("id") is None

    @_scopes()
    async def test_clear(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.clear`.
        """
        async with self._new_sut(scopes=scopes) as sut:
            await sut.set("id", next(self._values()))
            await sut.clear()
            assert await sut.get("id") is None
