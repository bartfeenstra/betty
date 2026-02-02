from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.data import Sample
from betty.locale.localizable.plain import Plain
from betty.sample import SampleNotFound, Samples, Size
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


_sample_full = Sample(object(), label=DUMMY_LOCALIZABLE, size=Size.FULL)
_sample_intermediate = Sample(object(), label=DUMMY_LOCALIZABLE)
_sample_minimal = Sample(object(), label=DUMMY_LOCALIZABLE, size=Size.MINIMAL)


class TestSample:
    def test_subject(self) -> None:
        data = object()
        sut = Sample(data, label=DUMMY_LOCALIZABLE)
        assert sut.subject is data

    def test_label(self) -> None:
        label = Plain("-")
        sut = Sample(object(), label=label)
        assert sut.label is label

    def test_description(self) -> None:
        description = Plain("-")
        sut = Sample(object(), label=DUMMY_LOCALIZABLE, description=description)
        assert sut.description is description

    def test_size(self) -> None:
        sut = Sample(object(), label=DUMMY_LOCALIZABLE, size=Size.MINIMAL)
        assert sut.size is Size.MINIMAL


class TestSamples:
    def test___iter__(self) -> None:
        assert list(
            iter(
                Samples(
                    [
                        lambda: _sample_minimal,
                        Samples([lambda: _sample_intermediate]),
                        lambda: _sample_full,
                    ]
                )
            )
        ) == [_sample_minimal, _sample_intermediate, _sample_full]

    @pytest.mark.parametrize(
        ("expected", "samples"),
        [
            (_sample_full, [lambda: _sample_full]),
            (_sample_full, [lambda: _sample_intermediate, lambda: _sample_full]),
            (_sample_full, [lambda: _sample_minimal, lambda: _sample_full]),
            (_sample_intermediate, [lambda: _sample_intermediate]),
            (
                _sample_intermediate,
                [lambda: _sample_minimal, lambda: _sample_intermediate],
            ),
            (_sample_minimal, [lambda: _sample_minimal]),
        ],
    )
    def test_get__full(
        self, expected: Sample, samples: Iterable[Callable[[], Sample] | Samples]
    ) -> None:
        assert Samples(samples).get(Size.FULL) is expected

    def test_get__full_without_samples(self) -> None:
        with pytest.raises(SampleNotFound):
            Samples([]).get(Size.FULL)

    @pytest.mark.parametrize(
        ("expected", "samples"),
        [
            (_sample_minimal, [lambda: _sample_minimal]),
            (_sample_minimal, [lambda: _sample_intermediate, lambda: _sample_minimal]),
            (_sample_minimal, [lambda: _sample_full, lambda: _sample_minimal]),
            (_sample_intermediate, [lambda: _sample_intermediate]),
            (
                _sample_intermediate,
                [lambda: _sample_full, lambda: _sample_intermediate],
            ),
            (_sample_full, [lambda: _sample_full]),
        ],
    )
    def test_get__minimal(
        self, expected: Sample, samples: Iterable[Callable[[], Sample] | Samples]
    ) -> None:
        assert Samples(samples).get(Size.MINIMAL) is expected

    def test_get__minimal_without_samples(self) -> None:
        with pytest.raises(SampleNotFound):
            Samples([]).get(Size.MINIMAL)
