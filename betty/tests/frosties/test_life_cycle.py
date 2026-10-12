from betty.frosties.life_cycle import FrozenOnBootstrap


class TestFrozenOnBootstrap:
    async def test_is_frozen(self) -> None:
        sut = FrozenOnBootstrap()
        assert not sut.is_frozen
        async with sut:
            assert sut.is_frozen
        assert sut.is_frozen
