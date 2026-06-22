from betty.store import StoreItem
from betty.stores.no_op import NoOpStore


class TestNoOpStore:
    async def test_with_scope(self) -> None:
        sut = NoOpStore()
        sut.with_scope("scopey")

    async def test_has(self) -> None:
        sut = NoOpStore()
        assert not await sut.has("id")

    async def test_hasset(self) -> None:
        sut = NoOpStore()
        async with sut.hasset("id") as result:
            assert result is not None
            await result("value")

    async def test_get(self) -> None:
        sut = NoOpStore()
        assert await sut.get("id") is None

    async def test_set(self) -> None:
        sut = NoOpStore()
        await sut.set("id", 123)

    async def test_set_with_modified(self) -> None:
        sut = NoOpStore()
        await sut.set("id", 123, modified=123456789)

    async def test_getset(self) -> None:
        sut = NoOpStore()
        async with sut.getset("id") as result:
            assert not isinstance(result, StoreItem)
            await result("value")

    async def test_delete(self) -> None:
        sut = NoOpStore()
        await sut.delete("id")

    async def test_clear(self) -> None:
        sut = NoOpStore()
        await sut.clear()
