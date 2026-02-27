import pytest

from betty.collection.keyed.adapter import (
    KeyedCollectionAdapter,
    MutableKeyedCollectionAdapter,
)
from betty.collection.keyed.error import (
    ErroringKeyedCollection,
    MutableErroringKeyedCollection,
)


class _KeyError(KeyError):
    pass


def _key_error(error: KeyError, key: str) -> KeyError:
    return _KeyError()


class TestErroringKeyedCollection:
    def test___getitem__(self) -> None:
        upstream = KeyedCollectionAdapter({"ONE": "one"})
        sut = ErroringKeyedCollection(upstream, _key_error)
        with pytest.raises(_KeyError):
            sut["TWO"]


class TestMutableErroringKeyedCollection:
    def test_remove(self) -> None:
        upstream = MutableKeyedCollectionAdapter(["one"], key=str.upper)
        sut = MutableErroringKeyedCollection(upstream, _key_error)
        with pytest.raises(_KeyError):
            sut.remove("TWO")

    def test___delitem__(self) -> None:
        upstream = MutableKeyedCollectionAdapter(["one"], key=str.upper)
        sut = MutableErroringKeyedCollection(upstream, _key_error)
        with pytest.raises(_KeyError):
            del sut["TWO"]
