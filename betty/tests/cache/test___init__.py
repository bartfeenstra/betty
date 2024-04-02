from asyncio import create_task, sleep
from collections.abc import Iterator
from typing import Sequence, AsyncContextManager, Generic

import pytest

from betty.cache import Cache, CacheItemValueT


class CacheTestBase(Generic[CacheItemValueT]):
    def _new_sut(
        self,
        *,
        scopes: Sequence[str] | None = None,
    ) -> AsyncContextManager[Cache[CacheItemValueT]]:
        raise NotImplementedError

    def _values(self) -> Iterator[CacheItemValueT]:
        raise NotImplementedError

    async def test_with_scope(self) -> None:
        async with self._new_sut() as sut:
            sut_with_scope = sut.with_scope('scopey')
            assert sut_with_scope is sut.with_scope('scopey')
            assert sut_with_scope is not sut

    @pytest.mark.parametrize('scopes', [
        (),
        ('scopey', 'dopey'),
    ])
    async def test_get_without_hit(self, scopes: Sequence[str]) -> None:
        async with self._new_sut(scopes=scopes) as sut:
            assert await sut.get('id') is None

    @pytest.mark.parametrize('scopes', [
        (),
        ('scopey', 'dopey'),
    ])
    async def test_set_and_get(self, scopes: Sequence[str]) -> None:
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set('id', value)
                cache_item = await sut.get('id')
                assert cache_item is not None
                assert await cache_item.value() == value

    @pytest.mark.parametrize('scopes', [
        (),
        ('scopey', 'dopey'),
    ])
    async def test_set_and_get_with_modified(self, scopes: Sequence[str]) -> None:
        modified = 123456789
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set('id', value, modified=modified)
                cache_item = await sut.get('id')
                assert cache_item is not None
                assert cache_item.modified == modified

    @pytest.mark.parametrize('scopes', [
        (),
        ('scopey', 'dopey'),
    ])
    async def test_getset_without_hit(self, scopes: Sequence[str]) -> None:
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                async with sut.getset('id') as (cache_item, setter):
                    assert cache_item is None
                    await setter(value)
                cache_item = await sut.get('id')
                assert cache_item is not None
                assert await cache_item.value() == value

    @pytest.mark.parametrize('scopes', [
        (),
        ('scopey', 'dopey'),
    ])
    async def test_getset_with_hit(self, scopes: Sequence[str]) -> None:
        for value in self._values():
            async with self._new_sut(scopes=scopes) as sut:
                await sut.set('id', value)
                async with sut.getset('id') as (cache_item, setter):
                    assert cache_item is not None
                    assert await cache_item.value() == value

    @pytest.mark.parametrize('scopes', [
        (),
        ('scopey', 'dopey'),
    ])
    async def test_getset_without_lock(self, scopes: Sequence[str]) -> None:
        async with self._new_sut(scopes=scopes) as sut:
            async def _acquire() -> None:
                async with sut.getset('id'):
                    await sleep(999)
            task = create_task(_acquire())
            await sleep(1)
            try:
                async with sut.getset('id', wait=False) as (cache_item, setter):
                    assert cache_item is None
                    assert setter is None
            finally:
                task.cancel()

    @pytest.mark.parametrize('scopes', [
        (),
        ('scopey', 'dopey'),
    ])
    async def test_delete(self, scopes: Sequence[str]) -> None:
        async with self._new_sut(scopes=scopes) as sut:
            await sut.set('id', next(self._values()))
            await sut.delete('id')
            assert await sut.get('id') is None

    @pytest.mark.parametrize('scopes', [
        (),
        ('scopey', 'dopey'),
    ])
    async def test_clear(self, scopes: Sequence[str]) -> None:
        async with self._new_sut(scopes=scopes) as sut:
            await sut.set('id', next(self._values()))
            await sut.clear()
            assert await sut.get('id') is None
