from betty import about


class TestVersion:
    def test(self):
        assert about.version() is None


class TestVersionLabel:
    def test(self):
        assert isinstance(about.version_label(), str)
