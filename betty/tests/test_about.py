from betty import about


class TestVersion:
    async def test(self) -> None:
        assert about.version() is None


class TestVersionLabel:
    async def test(self) -> None:
        assert isinstance(about.version_label(), str)
