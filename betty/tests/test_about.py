from betty import about


class TestVersion:
    def test(self) -> None:
        assert about.version() is None


class TestVersionLabel:
    def test(self) -> None:
        assert isinstance(about.version_label(), str)
