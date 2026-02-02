"""
Samples are used to generate documentation about various parts of Betty.
"""

from __future__ import annotations

from enum import IntEnum, auto
from typing import TYPE_CHECKING, Generic, Self, final

from typing_extensions import TypeVar

from betty.locale.localizable.resolve import resolve_localizable

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from betty.locale.localizable import Localizable, ResolvableLocalizable

_T = TypeVar("_T")


@final
class Size(IntEnum):
    """
    A sample size indicator.
    """

    MINIMAL = auto()
    INTERMEDIATE = auto()
    FULL = auto()


@final
class Sample(Generic[_T]):
    """
    A sample.

    Samples are useful for generating documentation and tests.
    """

    def __init__(
        self,
        subject: _T,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        size: Size = Size.INTERMEDIATE,
    ):
        self._subject = subject
        self._label = resolve_localizable(label)
        self._description = resolve_localizable(description) if description else None
        self._size = size

    @property
    def subject(self) -> _T:
        """
        The sample subject.
        """
        return self._subject

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
class Samples(Generic[_T]):
    """
    A set of samples.
    """

    def __init__(
        self,
        samples: Iterable[Callable[[], Sample[_T]] | Self],
    ):
        self._samples = list(samples)

    def __iter__(self) -> Iterator[Sample[_T]]:
        for sample in self._samples:
            if isinstance(sample, Samples):
                yield from sample
            else:
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
