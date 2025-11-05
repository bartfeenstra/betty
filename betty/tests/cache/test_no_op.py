from betty.cache import CacheItem
from betty.cache.no_op import NoOpCache


class TestNoOpCache:
    async def test_with_scope(self) -> None:
        sut = NoOpCache()
        sut.with_scope("scopey")

    async def test_has(self) -> None:
        sut = NoOpCache()
        assert not await sut.has("id")

    async def test_hasset(self) -> None:
        sut = NoOpCache()
        async with sut.hasset("id") as result:
            assert result is not None
            await result("value")

    async def test_get(self) -> None:
        sut = NoOpCache()
        assert await sut.get("id") is None

    async def test_set(self) -> None:
        sut = NoOpCache()
        await sut.set("id", 123)

    async def test_set_with_modified(self) -> None:
        sut = NoOpCache()
        await sut.set("id", 123, modified=123456789)

    async def test_getset(self) -> None:
        sut = NoOpCache()
        async with sut.getset("id") as result:
            assert not isinstance(result, CacheItem)
            await result("value")

    async def test_delete(self) -> None:
        sut = NoOpCache()
        await sut.delete("id")

    async def test_clear(self) -> None:
        sut = NoOpCache()
        await sut.clear()
