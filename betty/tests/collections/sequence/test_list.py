from betty.collections.sequence.list import List


class TestList:
    def test_resolve_value(self) -> None:
        sut = List(value=lambda value: value.upper())
        assert sut.resolve_value("Hello, world!") == "HELLO, WORLD!"
