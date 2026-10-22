import pytest

from betty.collections.catalog.dict import DictCatalog, FrozenDictCatalog
from betty.collections.catalog.error import ErroringCatalog, MutableErroringCatalog


class _KeyError(KeyError):
    pass


def _key_error(error: KeyError, key: str) -> KeyError:
    return _KeyError()


class TestErroringCatalog:
    def test___getitem__(self) -> None:
        proxied = FrozenDictCatalog({"ONE": "one"})
        sut = ErroringCatalog(proxied, _key_error)
        with pytest.raises(_KeyError):
            sut["TWO"]


class TestMutableErroringCatalog:
    def test_remove(self) -> None:
        proxied = DictCatalog(["one"], key=str.upper)
        sut = MutableErroringCatalog(proxied, _key_error)
        with pytest.raises(_KeyError):
            sut.remove("TWO")

    def test___delitem__(self) -> None:
        proxied = DictCatalog(["one"], key=str.upper)
        sut = MutableErroringCatalog(proxied, _key_error)
        with pytest.raises(_KeyError):
            del sut["TWO"]
