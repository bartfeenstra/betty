from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.sample import ResolvableSamples, Sample, SampleNotFound, Samples, Size

if TYPE_CHECKING:
    from collections.abc import Iterable


_sample_full = Sample(object, label="-", size=Size.FULL)
_sample_intermediate = Sample(object, label="-")
_sample_minimal = Sample(object, label="-", size=Size.MINIMAL)


class TestSample:
    def test_subject(self) -> None:
        data = object()
        sut = Sample(lambda: data, label="-")
        assert sut.subject is data

    def test_label(self) -> None:
        label = "My First Label"
        sut = Sample(object, label=label)
        assert sut.label == label

    def test_description(self) -> None:
        description = "My First Description"
        sut = Sample(object, label="-", description=description)
        assert sut.description == description

    def test_size(self) -> None:
        sut = Sample(object, label="-", size=Size.MINIMAL)
        assert sut.size is Size.MINIMAL


class TestSamples:
    def test___iter__(self) -> None:
        assert list(
            iter(
                Samples(
                    _sample_minimal,
                    Samples(_sample_intermediate),
                    _sample_full,
                )
            )
        ) == [
            _sample_minimal,
            _sample_intermediate,
            _sample_full,
        ]

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
    def test_get__full[SampleT](
        self, expected: Sample[SampleT], samples: Iterable[ResolvableSamples[SampleT]]
    ) -> None:
        assert Samples(*samples).get(Size.FULL) is expected

    def test_get__full_without_samples(self) -> None:
        with pytest.raises(SampleNotFound):
            Samples().get(Size.FULL)

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
    def test_get__minimal[SampleT](
        self, expected: Sample[SampleT], samples: Iterable[ResolvableSamples[SampleT]]
    ) -> None:
        assert Samples(*samples).get(Size.MINIMAL) is expected

    def test_get__minimal_without_samples(self) -> None:
        with pytest.raises(SampleNotFound):
            Samples().get(Size.MINIMAL)
