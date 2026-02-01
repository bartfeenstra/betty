from typing import Any

from betty.collections import (
    DictKeyedCollection,
    MutableDictKeyedCollection,
    MutableResolvedSequenceProxy,
    ResolvedSequenceProxy,
)
from betty.functools import passthrough


class TestDictKeyedCollection:
    def test___contains__(self) -> None:
        sut = DictKeyedCollection({"ONE": "one"})
        assert "ONE" in sut

    def test___contains____with_resolved_key(self) -> None:
        sut = DictKeyedCollection[str, Any, str]({"True": "True"}, key_resolver=str)
        assert True in sut

    def test___contains____with_invalid_value(self) -> None:
        sut = DictKeyedCollection[str, Any, str]({"True": "True"}, key_resolver=str)
        assert object() not in sut

    def test___getitem__(self) -> None:
        sut = DictKeyedCollection({"ONE": "one"})
        assert sut["ONE"] == "one"

    def test___getitem____with_resolved_key(self) -> None:
        sut = DictKeyedCollection[str, Any, str]({"True": "True"}, key_resolver=str)
        assert sut[True] == "True"

    def test___iter__(self) -> None:
        sut = DictKeyedCollection({"ONE": "one"})
        assert list(iter(sut)) == ["one"]

    def test___len__(self) -> None:
        sut = DictKeyedCollection({"ONE": "one"})
        assert len(sut) == 1

    def test_keys(self) -> None:
        sut = DictKeyedCollection({"ONE": "one"})
        assert list(sut.keys()) == ["ONE"]


class TestMutableDictKeyedCollection:
    def test___delitem__(self) -> None:
        sut = MutableDictKeyedCollection(["one"], key=lambda value: value.upper())
        del sut["ONE"]

    def test___delitem____with_resolved_key(self) -> None:
        sut = MutableDictKeyedCollection[str, Any, bool, str](
            ["True"], key=passthrough, key_resolver=str
        )
        del sut[True]

    def test_add__with_new_key(self) -> None:
        sut = MutableDictKeyedCollection[str, str, str, str](
            [], key=lambda value: value.upper()
        )
        sut.add("one")
        assert sut["ONE"] == "one"

    def test_add__with_existing_key(self) -> None:
        sut = MutableDictKeyedCollection(["one"], key=lambda value: value.upper())
        sut.add("ONE")
        assert sut["ONE"] == "ONE"

    def test_add__with_value_resolver(self) -> None:
        sut = MutableDictKeyedCollection[str, str, str, bool](
            [], key=passthrough, value_resolver=str
        )
        sut.add(True)
        assert sut["True"] == "True"

    def test_add__with_resolver(self) -> None:
        sut = MutableDictKeyedCollection[str, str, str, bool](
            [],
            key=passthrough,
            resolver=reversed,  # ty:ignore[invalid-argument-type]
        )
        sut.add(True, False)
        assert list(sut) == [False, True]

    def test_add__with_value_resolver_and_resolver(self) -> None:
        sut = MutableDictKeyedCollection[str, str, str, bool](
            [],
            key=passthrough,
            value_resolver=str,
            resolver=reversed,  # ty:ignore[invalid-argument-type]
        )
        sut.add(True, False)
        assert list(sut) == ["False", "True"]

    def test_clear(self) -> None:
        sut = MutableDictKeyedCollection(["one"], key=passthrough)
        sut.clear()
        assert list(sut) == []


class TestResolvedSequenceProxy:
    def test___getitem__(self) -> None:
        sut = ResolvedSequenceProxy(["True"], value_resolver=str)
        assert sut[0] == "True"

    def test___len__(self) -> None:
        sut = ResolvedSequenceProxy(["one"], value_resolver=passthrough)
        assert len(sut) == 1

    def test___contains__(self) -> None:
        sut = ResolvedSequenceProxy(["True"], value_resolver=str)
        assert True in sut

    def test___contains____with_invalid_value(self) -> None:
        def _resolver(value: Any) -> Any:
            raise Exception

        sut = ResolvedSequenceProxy([], value_resolver=_resolver)
        assert object() not in sut


class TestMutableResolvedSequenceProxy:
    def test_insert(self) -> None:
        upstream = []
        sut = MutableResolvedSequenceProxy(upstream, value_resolver=str)
        sut.insert(3, True)
        assert upstream == ["True"]

    def test_extend(self) -> None:
        upstream = ["False"]
        sut = MutableResolvedSequenceProxy(upstream, value_resolver=str)
        sut.extend([True])
        assert upstream == ["False", "True"]

    def test___setitem____with_index(self) -> None:
        upstream = ["True"]
        sut = MutableResolvedSequenceProxy(upstream, value_resolver=str)
        sut[0] = False
        assert upstream[0] == "False"

    def test___setitem____with_slice(self) -> None:
        upstream = ["True", "True", "True"]
        sut = MutableResolvedSequenceProxy(upstream, value_resolver=str)
        sut[1:3] = [False, False]
        assert upstream == ["True", "False", "False"]

    def test___delitem__(self) -> None:
        upstream = ["one"]
        sut = MutableResolvedSequenceProxy(upstream, value_resolver=passthrough)
        del sut[0]
        assert not upstream
