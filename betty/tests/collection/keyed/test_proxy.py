from betty.collection.keyed.adapter import (
    KeyedCollectionAdapter,
    MutableKeyedCollectionAdapter,
)
from betty.collection.keyed.proxy import (
    KeyedCollectionProxy,
    MutableKeyedCollectionProxy,
)


class TestKeyedCollectionProxy:
    def test___contains__(self) -> None:
        proxied = KeyedCollectionAdapter({"ONE": "one"})
        sut = KeyedCollectionProxy(proxied)
        assert "ONE" in sut

    def test___contains____with_invalid_value(self) -> None:
        proxied = KeyedCollectionAdapter({"TWO": "TWO"})
        sut = KeyedCollectionProxy(proxied)
        assert "ONE" not in sut

    def test___getitem__(self) -> None:
        proxied = KeyedCollectionAdapter({"ONE": "one"})
        sut = KeyedCollectionProxy(proxied)
        assert sut["ONE"] == "one"

    def test___iter__(self) -> None:
        proxied = KeyedCollectionAdapter({"ONE": "one"})
        sut = KeyedCollectionProxy(proxied)
        assert list(iter(sut)) == ["one"]

    def test___len__(self) -> None:
        proxied = KeyedCollectionAdapter({"ONE": "one"})
        sut = KeyedCollectionProxy(proxied)
        assert len(sut) == 1

    def test_keys(self) -> None:
        proxied = KeyedCollectionAdapter({"ONE": "one"})
        sut = KeyedCollectionProxy(proxied)
        assert list(sut.keys()) == ["ONE"]


class TestMutableKeyedCollectionProxy:
    def test_remove(self) -> None:
        proxied = MutableKeyedCollectionAdapter(["one", "two"], key=str.upper)
        sut = MutableKeyedCollectionProxy(proxied)
        sut.remove("ONE")
        assert list(proxied) == ["two"]
        assert list(proxied.keys()) == ["TWO"]

    def test___delitem__(self) -> None:
        proxied = MutableKeyedCollectionAdapter(["one", "two"], key=str.upper)
        sut = MutableKeyedCollectionProxy(proxied)
        del sut["ONE"]
        assert list(proxied) == ["two"]
        assert list(proxied.keys()) == ["TWO"]

    def test_add(self) -> None:
        proxied = MutableKeyedCollectionAdapter[str, str, str, str](
            ["one"], key=str.upper
        )
        sut = MutableKeyedCollectionProxy(proxied)
        sut.add("two")
        assert list(proxied) == ["one", "two"]
        assert list(proxied.keys()) == ["ONE", "TWO"]

    def test_clear(self) -> None:
        proxied = MutableKeyedCollectionAdapter(["one"], key=str.upper)
        sut = MutableKeyedCollectionProxy(proxied)
        sut.clear()
        assert list(sut) == []
