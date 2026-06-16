import pytest

from betty.collection.mapping.adapter import (
    MutableResolvedMappingAdapter,
    ResolvedMappingAdapter,
)
from betty.functools import passthrough


class TestResolvedMappingAdapter:
    def test___contains__(self) -> None:
        sut = ResolvedMappingAdapter(
            {"TRUE": "True"}, key_resolver=lambda key: str(key).upper()
        )
        assert True in sut
        assert False not in sut

    def test___getitem__(self) -> None:
        sut = ResolvedMappingAdapter(
            {"TRUE": "True"}, key_resolver=lambda key: str(key).upper()
        )
        assert sut[True] == "True"
        with pytest.raises(KeyError):
            sut[False]

    def test___iter__(self) -> None:
        sut = ResolvedMappingAdapter(
            {"TRUE": "True"}, key_resolver=lambda key: str(key).upper()
        )
        assert list(iter(sut)) == ["TRUE"]

    def test___len__(self) -> None:
        sut = ResolvedMappingAdapter(
            {"TRUE": "True"}, key_resolver=lambda key: str(key).upper()
        )
        assert len(sut) == 1

    def test_get(self) -> None:
        sut = ResolvedMappingAdapter(
            {"TRUE": "True"}, key_resolver=lambda key: str(key).upper()
        )
        assert sut.get(True) == "True"
        assert sut.get(False) is None
        default = object()
        assert sut.get(False, default) is default


class TestMutableResolvedMappingAdapter:
    def test___delitem__(self) -> None:
        proxied = {"TRUE": "True", "FALSE": "False"}
        sut = MutableResolvedMappingAdapter(
            proxied, key_resolver=lambda key: str(key).upper(), value_resolver=str
        )
        del sut[False]
        assert proxied == {"TRUE": "True"}

    def test___setitem__(self) -> None:
        proxied = {"TRUE": "True"}
        sut = MutableResolvedMappingAdapter(
            proxied, key_resolver=lambda key: str(key).upper(), value_resolver=str
        )
        sut[False] = False
        assert proxied == {"TRUE": "True", "FALSE": "False"}

    def test_pop(self) -> None:
        proxied = {"TRUE": "True", "FALSE": "False"}
        sut = MutableResolvedMappingAdapter(
            proxied, key_resolver=lambda key: str(key).upper(), value_resolver=str
        )
        assert sut.pop(True) == "True"

    def test_pop__with_default(self) -> None:
        proxied = {"TRUE": "True"}
        sut = MutableResolvedMappingAdapter(
            proxied, key_resolver=lambda key: str(key).upper(), value_resolver=str
        )
        assert sut.pop(False, "Hello, world!") == "Hello, world!"

    def test_popitem(self) -> None:
        proxied = {"TRUE": "True", "FALSE": "False"}
        sut = MutableResolvedMappingAdapter(
            proxied, key_resolver=passthrough, value_resolver=passthrough
        )
        assert sut.popitem() == ("FALSE", "False")
        assert proxied == {"TRUE": "True"}

    def test_setdefault(self) -> None:
        proxied = {"TRUE": "True"}
        sut = MutableResolvedMappingAdapter(
            proxied, key_resolver=lambda key: str(key).upper(), value_resolver=str
        )
        assert sut.setdefault(True, False) == "True"
        assert sut.setdefault(False, False) == "False"
        assert proxied == {"TRUE": "True", "FALSE": "False"}

    def test_update__with_mapping(self) -> None:
        proxied = {"TRUE": "True"}
        sut = MutableResolvedMappingAdapter(
            proxied, key_resolver=lambda key: str(key).upper(), value_resolver=str
        )
        sut.update({False: False})
        assert proxied == {"TRUE": "True", "FALSE": "False"}

    def test_update__with_iterable(self) -> None:
        proxied = {"TRUE": "True"}
        sut = MutableResolvedMappingAdapter(
            proxied, key_resolver=lambda key: str(key).upper(), value_resolver=str
        )
        sut.update([(False, False)])
        assert proxied == {"TRUE": "True", "FALSE": "False"}

    def test_update__with_kwargs(self) -> None:
        proxied = {"TRUE": "True"}
        sut = MutableResolvedMappingAdapter(
            proxied, key_resolver=lambda key: key.upper(), value_resolver=str
        )
        sut.update(false=False)
        assert proxied == {"TRUE": "True", "FALSE": "False"}
