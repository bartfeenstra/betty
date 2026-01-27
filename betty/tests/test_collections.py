from typing import Any

from betty.collections import KeyedCollection, ResolvingMutableSequence
from betty.functools import passthrough


class TestKeyedCollection:
    def test___contains__(self) -> None:
        sut = KeyedCollection(["one"], key=lambda value: value.upper())
        assert "ONE" in sut

    def test___contains____with_resolved_key(self) -> None:
        sut = KeyedCollection[str, str, bool, str](
            ["True"], key=passthrough, key_resolver=str
        )
        assert True in sut

    def test___contains____with_invalid_value(self) -> None:
        sut = KeyedCollection[str, str, bool, str](
            ["True"], key=passthrough, key_resolver=str
        )
        assert object() not in sut

    def test___getitem__(self) -> None:
        sut = KeyedCollection(["one"], key=lambda value: value.upper())
        assert sut["ONE"] == "one"

    def test___getitem____with_resolved_key(self) -> None:
        sut = KeyedCollection[str, str, bool, str](
            ["True"], key=passthrough, key_resolver=str
        )
        assert sut[True] == "True"

    def test___delitem__(self) -> None:
        sut = KeyedCollection(["one"], key=lambda value: value.upper())
        del sut["ONE"]

    def test___delitem____with_resolved_key(self) -> None:
        sut = KeyedCollection[str, str, bool, str](
            ["True"], key=passthrough, key_resolver=str
        )
        del sut[True]

    def test___iter__(self) -> None:
        sut = KeyedCollection(["one"], key=lambda value: value.upper())
        assert list(iter(sut)) == ["one"]

    def test___len__(self) -> None:
        sut = KeyedCollection(["one"], key=lambda value: value.upper())
        assert len(sut) == 1

    def test_add__with_new_key(self) -> None:
        sut = KeyedCollection[str, str, str, str]([], key=lambda value: value.upper())
        sut.add("one")
        assert sut["ONE"] == "one"

    def test_add__with_existing_key(self) -> None:
        sut = KeyedCollection(["one"], key=lambda value: value.upper())
        sut.add("ONE")
        assert sut["ONE"] == "ONE"

    def test_add__with_resolved_value(self) -> None:
        sut = KeyedCollection[str, str, str, bool](
            [], key=passthrough, value_resolver=str
        )
        sut.add(True)
        assert sut["True"] == "True"


class TestResolvingMutableSequence:
    def test_insert(self) -> None:
        decorated = []
        sut = ResolvingMutableSequence(decorated, str)
        sut.insert(3, True)
        assert decorated == ["True"]

    def test_extend(self) -> None:
        decorated = ["False"]
        sut = ResolvingMutableSequence(decorated, str)
        sut.extend([True])
        assert decorated == ["False", "True"]

    def test___getitem__(self) -> None:
        sut = ResolvingMutableSequence(["True"], str)
        assert sut[0] == "True"

    def test___setitem____with_index(self) -> None:
        decorated = ["True"]
        sut = ResolvingMutableSequence(decorated, str)
        sut[0] = False
        assert decorated[0] == "False"

    def test___setitem____with_slice(self) -> None:
        decorated = ["True", "True", "True"]
        sut = ResolvingMutableSequence(decorated, str)
        sut[1:3] = [False, False]
        assert decorated == ["True", "False", "False"]

    def test___delitem__(self) -> None:
        decorated = ["one"]
        sut = ResolvingMutableSequence(decorated, passthrough)
        del sut[0]
        assert not decorated

    def test___len__(self) -> None:
        sut = ResolvingMutableSequence(["one"], passthrough)
        assert len(sut) == 1

    def test___contains__(self) -> None:
        sut = ResolvingMutableSequence(["True"], str)
        assert True in sut

    def test___contains____with_invalid_value(self) -> None:
        def _resolver(value: Any) -> Any:
            raise Exception

        sut = ResolvingMutableSequence([], _resolver)
        assert object() not in sut
