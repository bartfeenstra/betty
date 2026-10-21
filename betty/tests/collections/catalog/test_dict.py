from betty.collections.catalog.dict import DictCatalog, FrozenDictCatalog


class TestFrozenDictCatalog:
    def test___hash__(self) -> None:
        assert hash(FrozenDictCatalog()) == hash(FrozenDictCatalog())
        assert hash(FrozenDictCatalog({"Hello": "world!"})) == hash(
            FrozenDictCatalog({"Hello": "world!"})
        )
        assert hash(FrozenDictCatalog()) != hash(FrozenDictCatalog({"Hello": "world!"}))


class TestDictCatalog:
    def test___init__(self) -> None:
        assert DictCatalog[str, str, str, str](
            lambda value: value * 2, ["Hello, world!"], key=str.upper, value=str.lower
        ).__wrapped__ == {"HELLO, WORLD!HELLO, WORLD!": "hello, world!"}
