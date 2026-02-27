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
        upstream = KeyedCollectionAdapter({"ONE": "one"})
        sut = KeyedCollectionProxy(upstream)
        assert "ONE" in sut

    def test___contains____with_invalid_value(self) -> None:
        upstream = KeyedCollectionAdapter({"TWO": "TWO"})
        sut = KeyedCollectionProxy(upstream)
        assert "ONE" not in sut

    def test___getitem__(self) -> None:
        upstream = KeyedCollectionAdapter({"ONE": "one"})
        sut = KeyedCollectionProxy(upstream)
        assert sut["ONE"] == "one"

    def test___iter__(self) -> None:
        upstream = KeyedCollectionAdapter({"ONE": "one"})
        sut = KeyedCollectionProxy(upstream)
        assert list(iter(sut)) == ["one"]

    def test___len__(self) -> None:
        upstream = KeyedCollectionAdapter({"ONE": "one"})
        sut = KeyedCollectionProxy(upstream)
        assert len(sut) == 1

    def test_keys(self) -> None:
        upstream = KeyedCollectionAdapter({"ONE": "one"})
        sut = KeyedCollectionProxy(upstream)
        assert list(sut.keys()) == ["ONE"]


class TestMutableKeyedCollectionProxy:
    def test_remove(self) -> None:
        upstream = MutableKeyedCollectionAdapter(["one", "two"], key=str.upper)
        sut = MutableKeyedCollectionProxy(upstream)
        sut.remove("ONE")
        assert list(upstream) == ["two"]
        assert list(upstream.keys()) == ["TWO"]

    def test___delitem__(self) -> None:
        upstream = MutableKeyedCollectionAdapter(["one", "two"], key=str.upper)
        sut = MutableKeyedCollectionProxy(upstream)
        del sut["ONE"]
        assert list(upstream) == ["two"]
        assert list(upstream.keys()) == ["TWO"]

    def test_add(self) -> None:
        upstream = MutableKeyedCollectionAdapter[str, str, str, str](
            ["one"], key=str.upper
        )
        sut = MutableKeyedCollectionProxy(upstream)
        sut.add("two")
        assert list(upstream) == ["one", "two"]
        assert list(upstream.keys()) == ["ONE", "TWO"]

    def test_clear(self) -> None:
        upstream = MutableKeyedCollectionAdapter(["one"], key=str.upper)
        sut = MutableKeyedCollectionProxy(upstream)
        sut.clear()
        assert list(sut) == []
