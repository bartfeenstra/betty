"""
Test utilities for :py:mod:`betty.cache`.
"""

import asyncio
import multiprocessing
import pickle
from asyncio import create_task, sleep
from collections.abc import Iterator, Sequence
from contextlib import AbstractAsyncContextManager
from typing import Any, Generic, TypeVar

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
    ) -> AbstractAsyncContextManager[Cache[_CacheItemValueT]]:
        raise NotImplementedError

    def _values(self) -> Iterator[_CacheItemValueT]:
        raise NotImplementedError

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
                async with sut_with_scope_two.get(cache_item_id) as cache_item:
                    assert cache_item
                    assert await cache_item.value() == value

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


class ProcesssafeCacheTestBase(
    Generic[_CacheItemValueT], CacheTestBase[_CacheItemValueT]
):
    """
    A base class for tests of :py:class:`betty.cache.Cache` implementations that are process-safe.
    """

    async def test_pickle(self) -> None:
        """
        Test that implementations can be pickled.
        """
        async with self._new_sut() as sut:
            pickle.loads(pickle.dumps(sut))

    @classmethod
    def _test_get_with_multiprocessing_target(
        cls, sut: Cache[_CacheItemValueT], cache_item_id: str, value: _CacheItemValueT
    ) -> None:
        asyncio.run(sut.set(cache_item_id, value))

    async def test_set_with_multiprocessing(self) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.set`.
        """
        for value in self._values():
            async with self._new_sut() as sut:
                process = multiprocessing.Process(
                    target=type(self)._test_get_with_multiprocessing_target,
                    args=(sut, "id", value),
                )
                process.start()
                process.join()
                async with sut.get("id") as cache_item:
                    assert cache_item
                    assert await cache_item.value() == value

    @classmethod
    def _test_delete_with_multiprocessing_target(
        cls, sut: Cache[_CacheItemValueT], cache_item_id: str
    ) -> None:
        asyncio.run(sut.delete(cache_item_id))

    async def test_delete_with_multiprocessing(self) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.delete`.
        """
        async with self._new_sut() as sut:
            await sut.set("id", next(self._values()))
            process = multiprocessing.Process(
                target=type(self)._test_delete_with_multiprocessing_target,
                args=(sut, "id"),
            )
            process.start()
            process.join()
            async with sut.get("id") as cache_item:
                assert cache_item is None

    @classmethod
    def _test_clear_with_multiprocessing_target(cls, sut: Cache[Any]):
        asyncio.run(sut.clear())

    async def test_clear_with_multiprocessing(self) -> None:
        """
        Test implementations of :py:meth:`betty.cache.Cache.clear`.
        """
        async with self._new_sut() as sut:
            await sut.set("id", next(self._values()))
            process = multiprocessing.Process(
                target=type(self)._test_clear_with_multiprocessing_target, args=(sut,)
            )
            process.start()
            process.join()
            async with sut.get("id") as cache_item:
                assert cache_item is None
