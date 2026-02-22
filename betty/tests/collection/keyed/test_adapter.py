from typing import Any

from betty.collection.keyed.adapter import (
    KeyedCollectionAdapter,
    MutableKeyedCollectionAdapter,
)
from betty.functools import passthrough


class TestKeyedCollectionAdapter:
    def test___contains__(self) -> None:
        sut = KeyedCollectionAdapter(
            {"ONE": "one"}, key_resolver=lambda key: str(key).upper()
        )
        assert "ONE" in sut

    def test___contains____with_resolved_key(self) -> None:
        sut = KeyedCollectionAdapter(
            {"TRUE": "True"}, key_resolver=lambda key: str(key).upper()
        )
        assert True in sut

    def test___contains____with_invalid_value(self) -> None:
        sut = KeyedCollectionAdapter(
            {"TRUE": "True"}, key_resolver=lambda key: str(key).upper()
        )
        assert object() not in sut

    def test___getitem__(self) -> None:
        sut = KeyedCollectionAdapter({"ONE": "one"})
        assert sut["ONE"] == "one"

    def test___getitem____with_resolved_key(self) -> None:
        sut = KeyedCollectionAdapter(
            {"TRUE": "True"}, key_resolver=lambda key: str(key).upper()
        )
        assert sut[True] == "True"

    def test___iter__(self) -> None:
        sut = KeyedCollectionAdapter({"ONE": "one"})
        assert list(iter(sut)) == ["one"]

    def test___len__(self) -> None:
        sut = KeyedCollectionAdapter({"ONE": "one"})
        assert len(sut) == 1

    def test_keys(self) -> None:
        sut = KeyedCollectionAdapter({"ONE": "one"})
        assert list(sut.keys()) == ["ONE"]


class TestMutableKeyedCollectionAdapter:
    def test_remove(self) -> None:
        sut = MutableKeyedCollectionAdapter(["one"], key=lambda value: value.upper())
        sut.remove("ONE")
        assert not sut

    def test___delitem__(self) -> None:
        sut = MutableKeyedCollectionAdapter(["one"], key=lambda value: value.upper())
        del sut["ONE"]

    def test___delitem____with_resolved_key(self) -> None:
        sut = MutableKeyedCollectionAdapter[str, Any, bool, str](
            ["True"], key=passthrough, key_resolver=str
        )
        del sut[True]

    def test_add__with_new_key(self) -> None:
        sut = MutableKeyedCollectionAdapter[str, str, str, str](
            [], key=lambda value: value.upper()
        )
        sut.add("one")
        assert sut["ONE"] == "one"

    def test_add__with_existing_key(self) -> None:
        sut = MutableKeyedCollectionAdapter(["one"], key=lambda value: value.upper())
        sut.add("ONE")
        assert sut["ONE"] == "ONE"

    def test_add__with_value_resolver(self) -> None:
        sut = MutableKeyedCollectionAdapter[str, str, str, bool](
            [], key=passthrough, value_resolver=str
        )
        sut.add(True)
        assert sut["True"] == "True"

    def test_clear(self) -> None:
        sut = MutableKeyedCollectionAdapter(["one"], key=passthrough)
        sut.clear()
        assert list(sut) == []
