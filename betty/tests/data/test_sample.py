from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.data import DataDefinition, Sample, SampleNotFound
from betty.data.sample import get_full_sample, get_minimal_sample
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE

if TYPE_CHECKING:
    from betty.config import Configuration


_sample_full = Sample(object(), label=DUMMY_LOCALIZABLE, full=True)
_sample_undetermined = Sample(object(), label=DUMMY_LOCALIZABLE)
_sample_minimal = Sample(object(), label=DUMMY_LOCALIZABLE, minimal=True)


@pytest.mark.parametrize(
    ("expected", "data"),
    [
        (
            _sample_full,
            DataDefinition(
                cls=object, label=DUMMY_LOCALIZABLE, samples=[lambda: _sample_full]
            ),
        ),
        (
            _sample_full,
            DataDefinition(
                cls=object,
                label=DUMMY_LOCALIZABLE,
                samples=[lambda: _sample_undetermined, lambda: _sample_full],
            ),
        ),
        (
            _sample_full,
            DataDefinition(
                cls=object,
                label=DUMMY_LOCALIZABLE,
                samples=[lambda: _sample_minimal, lambda: _sample_full],
            ),
        ),
        (
            _sample_undetermined,
            DataDefinition(
                cls=object,
                label=DUMMY_LOCALIZABLE,
                samples=[lambda: _sample_undetermined],
            ),
        ),
        (
            _sample_undetermined,
            DataDefinition(
                cls=object,
                label=DUMMY_LOCALIZABLE,
                samples=[lambda: _sample_minimal, lambda: _sample_undetermined],
            ),
        ),
        (
            _sample_minimal,
            DataDefinition(
                cls=object, label=DUMMY_LOCALIZABLE, samples=[lambda: _sample_minimal]
            ),
        ),
    ],
)
def test_get_full_sample(
    expected: Sample[object], data: DataDefinition[object] | type[Configuration]
) -> None:
    assert get_full_sample(data) is expected


@pytest.mark.parametrize(
    "data",
    [
        DataDefinition(cls=object, label=DUMMY_LOCALIZABLE),
    ],
)
def test_get_full_sample__without_samples(
    data: DataDefinition[object] | type[Configuration],
) -> None:
    with pytest.raises(SampleNotFound):
        get_full_sample(data)


@pytest.mark.parametrize(
    ("expected", "data"),
    [
        (
            _sample_minimal,
            DataDefinition(
                cls=object, label=DUMMY_LOCALIZABLE, samples=[lambda: _sample_minimal]
            ),
        ),
        (
            _sample_minimal,
            DataDefinition(
                cls=object,
                label=DUMMY_LOCALIZABLE,
                samples=[lambda: _sample_undetermined, lambda: _sample_minimal],
            ),
        ),
        (
            _sample_minimal,
            DataDefinition(
                cls=object,
                label=DUMMY_LOCALIZABLE,
                samples=[lambda: _sample_full, lambda: _sample_minimal],
            ),
        ),
        (
            _sample_undetermined,
            DataDefinition(
                cls=object,
                label=DUMMY_LOCALIZABLE,
                samples=[lambda: _sample_undetermined],
            ),
        ),
        (
            _sample_undetermined,
            DataDefinition(
                cls=object,
                label=DUMMY_LOCALIZABLE,
                samples=[lambda: _sample_full, lambda: _sample_undetermined],
            ),
        ),
        (
            _sample_full,
            DataDefinition(
                cls=object, label=DUMMY_LOCALIZABLE, samples=[lambda: _sample_full]
            ),
        ),
    ],
)
def test_get_minimal_sample(
    expected: Sample[object], data: DataDefinition[object] | type[Configuration]
) -> None:
    assert get_minimal_sample(data) is expected


@pytest.mark.parametrize(
    "data",
    [
        DataDefinition(cls=object, label=DUMMY_LOCALIZABLE),
    ],
)
def test_get_minimal_sample__without_samples(
    data: DataDefinition[object] | type[Configuration],
) -> None:
    with pytest.raises(SampleNotFound):
        get_minimal_sample(data)
