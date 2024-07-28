"""
Test utilities for :py:mod:`betty.cache`.
"""

from asyncio import sleep, create_task
from typing import Generic, Sequence, AsyncContextManager, Iterator, TypeVar

import pytest

from betty.cache import Cache


_CacheItemValueT = TypeVar("_CacheItemValueT")


class CacheTestBase(Generic[_CacheItemValueT]):
    """
    A base class for tests of :py:class:`betty.cache.Cache` implementations.
    """

    def _new_sut(
        self,
        *,
        scopes: Sequence[str] | None = None,
    ) -> AsyncContextManager[Cache[_CacheItemValueT]]:
        raise NotImplementedError

    def _values(self) -> Iterator[_CacheItemValueT]:
        raise NotImplementedError

    async def test_with_scope(self) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.with_scope`.
        """
        async with self._new_sut() as sut:
            sut_with_scope = sut.with_scope("scopey")
            assert sut_with_scope is sut.with_scope("scopey")
            assert sut_with_scope is not sut

    @pytest.mark.parametrize(
        "scopes",
        [
            (),
            ("scopey", "dopey"),
        ],
    )
    async def test_get_without_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.get`.
        """
        async with self._new_sut(scopes=scopes) as sut, sut.get("id") as cache_item:
            assert cache_item is None

    @pytest.mark.parametrize(
        "scopes",
        [
            (),
            ("scopey", "dopey"),
        ],
    )
    async def test_set_and_get(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.get` and :py:meth:`betty.cache.Cache.set`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set("id", value)
                async with sut.get("id") as cache_item:
                    assert cache_item is not None
                    assert await cache_item.value() == value

    @pytest.mark.parametrize(
        "scopes",
        [
            (),
            ("scopey", "dopey"),
        ],
    )
    async def test_set_and_get_with_modified(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.get` and :py:meth:`betty.cache.Cache.set`.
        """
        modified = 123456789
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set("id", value, modified=modified)
                async with sut.get("id") as cache_item:
                    assert cache_item is not None
                    assert cache_item.modified == modified

    @pytest.mark.parametrize(
        "scopes",
        [
            (),
            ("scopey", "dopey"),
        ],
    )
    async def test_getset_without_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.getset`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                async with sut.getset("id") as (cache_item, setter):
                    assert cache_item is None
                    await setter(value)
                async with sut.get("id") as cache_item:
                    assert cache_item is not None
                    assert await cache_item.value() == value

    @pytest.mark.parametrize(
        "scopes",
        [
            (),
            ("scopey", "dopey"),
        ],
    )
    async def test_getset_with_hit(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.getset`.
        """
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set("id", value)
                async with sut.getset("id") as (cache_item, setter):
                    assert cache_item is not None
                    assert await cache_item.value() == value

    @pytest.mark.parametrize(
        "scopes",
        [
            (),
            ("scopey", "dopey"),
        ],
    )
    async def test_getset_without_lock(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.getset`.
        """
        async with self._new_sut(scopes=scopes) as sut:

            async def _acquire() -> None:
                async with sut.getset("id"):
                    await sleep(999)

            task = create_task(_acquire())
            await sleep(1)
            try:
                async with sut.getset("id", wait=False) as (cache_item, setter):
                    assert cache_item is None
                    assert setter is None
            finally:
                task.cancel()

    @pytest.mark.parametrize(
        "scopes",
        [
            (),
            ("scopey", "dopey"),
        ],
    )
    async def test_delete(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.delete`.
        """
        async with self._new_sut(scopes=scopes) as sut:
            await sut.set("id", next(self._values()))
            await sut.delete("id")
            async with sut.get("id") as cache_item:
                assert cache_item is None

    @pytest.mark.parametrize(
        "scopes",
        [
            (),
            ("scopey", "dopey"),
        ],
    )
    async def test_clear(self, scopes: Sequence[str]) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.clear`.
        """
        async with self._new_sut(scopes=scopes) as sut:
            await sut.set("id", next(self._values()))
            await sut.clear()
            async with sut.get("id") as cache_item:
                assert cache_item is None
