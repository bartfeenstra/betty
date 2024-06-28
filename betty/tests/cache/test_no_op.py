from betty.cache.no_op import NoOpCache


class TestNoOpCache:
    async def test_with_scope(self) -> None:
        sut = NoOpCache()
        sut.with_scope("scopey")

    async def test_get(self) -> None:
        sut = NoOpCache()
        async with sut.get("id") as cache_item:
            assert cache_item is None

    async def test_set(self) -> None:
        sut = NoOpCache()
        await sut.set("id", 123)

    async def test_set_with_modified(self) -> None:
        sut = NoOpCache()
        await sut.set("id", 123, modified=123456789)

    async def test_getset(self) -> None:
        sut = NoOpCache()
        async with sut.getset("id") as (cache_item, setter):
            assert cache_item is None
            await setter(123)

    async def test_getset_without_wait(self) -> None:
        sut = NoOpCache()
        async with sut.getset("id", wait=False) as (cache_item, setter):
            assert cache_item is None
            assert setter is None

    async def test_delete(self) -> None:
        sut = NoOpCache()
        await sut.delete("id")

    async def test_clear(self) -> None:
        sut = NoOpCache()
        await sut.clear()
