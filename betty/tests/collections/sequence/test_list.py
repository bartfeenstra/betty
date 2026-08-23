from betty.collections.sequence.list import ResolvedList


class TestResolvedList:
    def test__resolver(self) -> None:
        sut = ResolvedList(value_resolver=lambda value: value.upper())
        sut.append("Hello, world!")
        assert list(sut) == ["HELLO, WORLD!"]
