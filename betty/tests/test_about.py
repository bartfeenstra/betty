from betty import about


class TestVersion:
    async def test(self) -> None:
        assert about.version()


class TestVersionLabel:
    async def test(self) -> None:
        assert about.version_label()
