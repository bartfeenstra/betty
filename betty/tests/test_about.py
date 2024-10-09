from betty import about


class TestVersion:
    async def test(self) -> None:
        assert about.version()


class TestVersionLabel:
    async def test(self) -> None:
        assert about.version_label()


class TestIsDevelopment:
    def test(self) -> None:
        assert about.is_development()


class TestIsStable:
    def test(self) -> None:
        assert not about.is_stable()


class TestReport:
    def test(self) -> None:
        assert len(about.report().split("\n"))
