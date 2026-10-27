from typing import Any, override

import pytest

from betty.collections.sequence.adapter import MutableSequenceAdapter, SequenceAdapter


class _SequenceAdapter(SequenceAdapter[str, Any, list[str]]):
    @override
    def resolve_value(self, value: Any, /) -> str:
        return str(value)


class TestSequenceAdapter:
    def test___getitem__(self) -> None:
        sut = _SequenceAdapter(["True"])
        assert sut[0] == "True"

    def test___len__(self) -> None:
        sut = _SequenceAdapter(["one"])
        assert len(sut) == 1

    def test___contains__(self) -> None:
        sut = _SequenceAdapter(["True"])
        assert True in sut

    def test___contains____with_invalid_value(self) -> None:
        class _Unstringable:
            def __str__(self) -> str:
                raise RuntimeError

        sut = _SequenceAdapter([])
        assert _Unstringable() not in sut

    def test_index(self) -> None:
        sut = _SequenceAdapter(["NotTrue", "True", "True"])
        assert sut.index(True) == 1

    def test_index__with_start(self) -> None:
        sut = _SequenceAdapter(["True", "NotTrue", "True"])
        assert sut.index(True, 1) == 2

    def test_index__with_stop(self) -> None:
        sut = _SequenceAdapter(["NotTrue", "True"])
        with pytest.raises(
            ValueError,  # noqa: PT011
        ):
            sut.index(True, 0, 1)


class _MutableSequenceAdapter(
    _SequenceAdapter, MutableSequenceAdapter[str, Any, list[str]]
):
    pass


class TestMutableSequenceAdapter:
    def test_insert(self) -> None:
        proxied = []
        sut = _MutableSequenceAdapter(proxied)
        sut.insert(3, True)
        assert proxied == ["True"]

    def test_extend(self) -> None:
        proxied = ["False"]
        sut = _MutableSequenceAdapter(proxied)
        sut.extend([True])
        assert proxied == ["False", "True"]

    def test___setitem____with_index(self) -> None:
        proxied = ["True"]
        sut = _MutableSequenceAdapter(proxied)
        sut[0] = False
        assert proxied[0] == "False"

    def test___setitem____with_slice(self) -> None:
        proxied = ["True", "True", "True"]
        sut = _MutableSequenceAdapter(proxied)
        sut[1:3] = [False, False]
        assert proxied == ["True", "False", "False"]

    def test___delitem__(self) -> None:
        proxied = ["one"]
        sut = _MutableSequenceAdapter(proxied)
        del sut[0]
        assert not proxied
