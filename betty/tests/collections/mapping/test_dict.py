from betty.collections.mapping.dict import Dict, FrozenDict


class TestFrozenDict:
    def test_resolve_key(self) -> None:
        assert FrozenDict(key=str.upper).resolve_key("one") == "ONE"

    def test___hash__(self) -> None:
        assert hash(FrozenDict()) == hash(FrozenDict())
        assert hash(FrozenDict({"Hello": "world!"})) == hash(
            FrozenDict({"Hello": "world!"})
        )
        assert hash(FrozenDict()) != hash(FrozenDict({"Hello": "world!"}))


class TestDict:
    def test_resolve_key(self) -> None:
        assert Dict(key=str.upper).resolve_key("one") == "ONE"

    def test_resolve_value(self) -> None:
        assert Dict(value=str.upper).resolve_value("one") == "ONE"
