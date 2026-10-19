from betty.collections.sequence.list import List


class TestResolvedList:
    def test__resolver(self) -> None:
        sut = List(value_resolver=lambda value: value.upper())
        sut.append("Hello, world!")
        assert list(sut) == ["HELLO, WORLD!"]
