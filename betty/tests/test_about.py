from betty import about


class TestVersion:
    async def test(self) -> None:
        assert await about.version() is None


class TestVersionLabel:
    async def test(self) -> None:
        assert isinstance(await about.version_label(), str)
