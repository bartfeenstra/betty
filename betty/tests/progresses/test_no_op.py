from betty.progresses.no_op import NoOpProgress


class TestNoOpProgress:
    async def test_add(self) -> None:
        sut = NoOpProgress()
        await sut.add()

    async def test_done(self) -> None:
        sut = NoOpProgress()
        await sut.done()
