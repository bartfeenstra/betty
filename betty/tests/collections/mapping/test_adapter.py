from typing import Any, override

import pytest

from betty.collections.mapping.adapter import MappingAdapter, MutableMappingAdapter


class _MappingAdapter(MappingAdapter[str, Any, str, dict[str, str]]):
    @override
    def resolve_key(self, key: Any, /) -> str:
        return str(key).upper()


class TestMappingAdapter:
    def test___contains__(self) -> None:
        sut = _MappingAdapter({"TRUE": "True"})
        assert True in sut
        assert False not in sut

    def test___getitem__(self) -> None:
        sut = _MappingAdapter({"TRUE": "True"})
        assert sut[True] == "True"
        with pytest.raises(KeyError):
            sut[False]

    def test___iter__(self) -> None:
        sut = _MappingAdapter({"TRUE": "True"})
        assert list(iter(sut)) == ["TRUE"]

    def test___len__(self) -> None:
        sut = _MappingAdapter({"TRUE": "True"})
        assert len(sut) == 1

    def test_get(self) -> None:
        sut = _MappingAdapter({"TRUE": "True"})
        assert sut.get(True) == "True"
        assert sut.get(False) is None
        default = object()
        assert sut.get(False, default) is default


class _MutableMappingAdapter(
    _MappingAdapter, MutableMappingAdapter[str, Any, str, Any, dict[str, str]]
):
    @override
    def resolve_value(self, value: Any, /) -> str:
        return str(value)


class TestMutableMappingAdapter:
    def test___delitem__(self) -> None:
        proxied = {"TRUE": "True", "FALSE": "False"}
        sut = _MutableMappingAdapter(proxied)
        del sut[False]
        assert proxied == {"TRUE": "True"}

    def test___setitem__(self) -> None:
        proxied = {"TRUE": "True"}
        sut = _MutableMappingAdapter(proxied)
        sut[False] = False
        assert proxied == {"TRUE": "True", "FALSE": "False"}

    def test_pop(self) -> None:
        proxied = {"TRUE": "True", "FALSE": "False"}
        sut = _MutableMappingAdapter(proxied)
        assert sut.pop(True) == "True"

    def test_pop__with_default(self) -> None:
        proxied = {"TRUE": "True"}
        sut = _MutableMappingAdapter(proxied)
        assert sut.pop(False, "Hello, world!") == "Hello, world!"

    def test_popitem(self) -> None:
        proxied = {"TRUE": "True", "FALSE": "False"}
        sut = _MutableMappingAdapter(proxied)
        assert sut.popitem() == ("FALSE", "False")
        assert proxied == {"TRUE": "True"}

    def test_setdefault(self) -> None:
        proxied = {"TRUE": "True"}
        sut = _MutableMappingAdapter(proxied)
        assert sut.setdefault(True, False) == "True"
        assert sut.setdefault(False, False) == "False"
        assert proxied == {"TRUE": "True", "FALSE": "False"}

    def test_update__with_mapping(self) -> None:
        proxied = {"TRUE": "True"}
        sut = _MutableMappingAdapter(proxied)
        sut.update({False: False})
        assert proxied == {"TRUE": "True", "FALSE": "False"}

    def test_update__with_iterable(self) -> None:
        proxied = {"TRUE": "True"}
        sut = _MutableMappingAdapter(proxied)
        sut.update([(False, False)])
        assert proxied == {"TRUE": "True", "FALSE": "False"}

    def test_update__with_kwargs(self) -> None:
        proxied = {"TRUE": "True"}
        sut = _MutableMappingAdapter(proxied)
        sut.update(false=False)
        assert proxied == {"TRUE": "True", "FALSE": "False"}
