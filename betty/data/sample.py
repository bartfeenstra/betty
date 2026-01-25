"""
Data sample helpers.
"""

from __future__ import annotations

from enum import IntEnum, auto
from typing import TYPE_CHECKING, Any, Generic, final

from typing_extensions import TypeVar

from betty.locale.localizable.ensure import ensure_localizable

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from betty.locale.localizable import Localizable, LocalizableLike

_DataClsT = TypeVar("_DataClsT", default=Any)


@final
class Size(IntEnum):
    """
    A sample size indicator.
    """

    MINIMAL = auto()
    INTERMEDIATE = auto()
    FULL = auto()


@final
class Sample(Generic[_DataClsT]):
    """
    A data sample.

    Samples are useful for generating documentation and tests.
    """

    def __init__(
        self,
        data: _DataClsT,
        *,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
        size: Size = Size.INTERMEDIATE,
    ):
        self._data = data
        self._label = ensure_localizable(label)
        self._description = ensure_localizable(description) if description else None
        self._size = size

    @property
    def data(self) -> _DataClsT:
        """
        The sample data.
        """
        return self._data

    @property
    def label(self) -> Localizable:
        """
        The sample's human-readable short label.
        """
        return self._label

    @property
    def description(self) -> Localizable | None:
        """
        The sample's human-readable long description.
        """
        return self._description

    @property
    def size(self) -> Size:
        """
        The sample size.
        """
        return self._size


@final
class Samples(Generic[_DataClsT]):
    """
    A set of samples.
    """

    def __init__(
        self,
        samples: Iterable[Callable[[], Sample[_DataClsT]]],
    ):
        self._samples = list(samples)

    def __iter__(self) -> Iterator[Sample[_DataClsT]]:
        for sample in self._samples:
            yield sample()

    def get(self, preferred_size: Size = Size.INTERMEDIATE, /):
        """
        Get a sample.
        """
        samples = sorted(self, key=lambda sample: abs(preferred_size - sample.size))
        if samples:
            return samples[0]
        raise SampleNotFound


class SampleNotFound(Exception):
    """
    Raised when a sample could not be found.
    """
