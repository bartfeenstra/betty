from betty import about


class TestVersion:
    def test(self):
        assert isinstance(about.version(), str)
