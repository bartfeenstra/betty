from betty.collections.sequence.list import List


class TestList:
    def test__resolver(self) -> None:
        sut = List(value=lambda value: value.upper())
        sut.append("Hello, world!")
        assert list(sut) == ["HELLO, WORLD!"]
