from betty.collections.catalog.dict import DictCatalog, FrozenDictCatalog
from betty.collections.catalog.proxy import CatalogProxy, MutableCatalogProxy


class TestCatalogProxy:
    def test___contains__(self) -> None:
        proxied = FrozenDictCatalog(str.upper, {"ONE": "one"})
        sut = CatalogProxy(proxied)
        assert "ONE" in sut

    def test___contains____with_invalid_value(self) -> None:
        proxied = FrozenDictCatalog(str.upper, {"TWO": "TWO"})
        sut = CatalogProxy(proxied)
        assert "ONE" not in sut

    def test___getitem__(self) -> None:
        proxied = FrozenDictCatalog(str.upper, {"ONE": "one"})
        sut = CatalogProxy(proxied)
        assert sut["ONE"] == "one"

    def test___iter__(self) -> None:
        proxied = FrozenDictCatalog(str.upper, {"ONE": "one"})
        sut = CatalogProxy(proxied)
        assert list(iter(sut)) == ["one"]

    def test___len__(self) -> None:
        proxied = FrozenDictCatalog(str.upper, {"ONE": "one"})
        sut = CatalogProxy(proxied)
        assert len(sut) == 1

    def test_keys(self) -> None:
        proxied = FrozenDictCatalog(str.upper, {"ONE": "one"})
        sut = CatalogProxy(proxied)
        assert list(sut.keys()) == ["ONE"]


class TestMutableCatalogProxy:
    def test_remove(self) -> None:
        proxied = DictCatalog(str.upper, ["one", "two"])
        sut = MutableCatalogProxy(proxied)
        sut.remove("ONE")
        assert list(proxied) == ["two"]
        assert list(proxied.keys()) == ["TWO"]

    def test___delitem__(self) -> None:
        proxied = DictCatalog(str.upper, ["one", "two"])
        sut = MutableCatalogProxy(proxied)
        del sut["ONE"]
        assert list(proxied) == ["two"]
        assert list(proxied.keys()) == ["TWO"]

    def test_add(self) -> None:
        proxied = DictCatalog[str, str, str, str](str.upper, ["one"])
        sut = MutableCatalogProxy(proxied)
        sut.add("two")
        assert list(proxied) == ["one", "two"]
        assert list(proxied.keys()) == ["ONE", "TWO"]

    def test_clear(self) -> None:
        proxied = DictCatalog(str.upper, ["one"])
        sut = MutableCatalogProxy(proxied)
        sut.clear()
        assert list(sut) == []
