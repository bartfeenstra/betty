from typing import Any

import pytest

from betty.collection.sequence.adapter import (
    MutableResolvedSequenceAdapter,
    ResolvedSequenceAdapter,
)
from betty.functools import passthrough


class TestResolvedSequenceAdapter:
    def test___getitem__(self) -> None:
        sut = ResolvedSequenceAdapter(["True"], value_resolver=str)
        assert sut[0] == "True"

    def test___len__(self) -> None:
        sut = ResolvedSequenceAdapter(["one"], value_resolver=passthrough)
        assert len(sut) == 1

    def test___contains__(self) -> None:
        sut = ResolvedSequenceAdapter(["True"], value_resolver=str)
        assert True in sut

    def test___contains____with_invalid_value(self) -> None:
        def _resolver(value: Any) -> Any:
            raise Exception  # noqa: TRY002

        sut = ResolvedSequenceAdapter([], value_resolver=_resolver)
        assert object() not in sut

    def test_index(self) -> None:
        sut = ResolvedSequenceAdapter(["NotTrue", "True", "True"], value_resolver=str)
        assert sut.index(True) == 1

    def test_index__with_start(self) -> None:
        sut = ResolvedSequenceAdapter(["True", "NotTrue", "True"], value_resolver=str)
        assert (
            sut.index(
                True,
                1,
            )
            == 2
        )

    def test_index__with_stop(self) -> None:
        sut = ResolvedSequenceAdapter(["NotTrue", "True"], value_resolver=str)
        with pytest.raises(
            ValueError,  # noqa: PT011
        ):
            sut.index(True, 0, 1)


class TestMutableResolvedSequenceAdapter:
    def test_insert(self) -> None:
        upstream = []
        sut = MutableResolvedSequenceAdapter(upstream, value_resolver=str)
        sut.insert(3, True)
        assert upstream == ["True"]

    def test_extend(self) -> None:
        upstream = ["False"]
        sut = MutableResolvedSequenceAdapter(upstream, value_resolver=str)
        sut.extend([True])
        assert upstream == ["False", "True"]

    def test___setitem____with_index(self) -> None:
        upstream = ["True"]
        sut = MutableResolvedSequenceAdapter(upstream, value_resolver=str)
        sut[0] = False
        assert upstream[0] == "False"

    def test___setitem____with_slice(self) -> None:
        upstream = ["True", "True", "True"]
        sut = MutableResolvedSequenceAdapter(upstream, value_resolver=str)
        sut[1:3] = [False, False]
        assert upstream == ["True", "False", "False"]

    def test___delitem__(self) -> None:
        upstream = ["one"]
        sut = MutableResolvedSequenceAdapter(upstream, value_resolver=passthrough)
        del sut[0]
        assert not upstream
