from __future__ import annotations

from typing import override

from betty.pipeline import Inlet, Pipeline, Vent


class _Pipeline(Pipeline[int, int]):
    @override
    def __call__(self, value: int, /) -> int:
        return value + 1


class TestPipeline:
    def test_pipe(self) -> None:
        sut = _Pipeline().pipe(lambda value: value + 3)
        assert sut(123) == 127

    def test___or__(self) -> None:
        sut = _Pipeline() | (lambda value: value + 3)
        assert sut(123) == 127

    def test_vent(self) -> None:
        carrier = []
        sut = (
            _Pipeline()
            .vent(lambda value: carrier.append(value + 3))
            .pipe(lambda value: value + 5)
        )
        assert sut(123) == 129
        assert carrier == [127]

    def test___truediv__(self) -> None:
        carrier = []
        sut = _Pipeline() / (lambda value: carrier.append(value + 3)) | (
            lambda value: value + 5
        )
        assert sut(123) == 129
        assert carrier == [127]


class TestInlet:
    def test___call__(self) -> None:
        sut = Inlet[int, int](lambda value: value + 1)
        assert sut(123) == 124


class TestVent:
    def test___call__(self) -> None:
        carrier = []
        sut = Vent[int](lambda value: carrier.append(value + 1))
        assert sut(123) == 123
        assert carrier == [124]
