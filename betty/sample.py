"""
Samples are used to generate documentation about various parts of Betty.
"""

from __future__ import annotations

from enum import IntEnum, auto
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from betty.localizer import AnyLocalizable


@final
class Size(IntEnum):
    """
    A sample size indicator.
    """

    MINIMAL = auto()
    INTERMEDIATE = auto()
    FULL = auto()


@final
class Sample[T]:
    """
    A sample.

    Samples are useful for generating documentation and tests.
    """

    def __init__(
        self,
        subject: T,
        *,
        label: AnyLocalizable,
        description: AnyLocalizable | None = None,
        size: Size = Size.INTERMEDIATE,
    ):
        self.subject: Final[T] = subject
        """
        The sample subject.
        """
        self.label: Final[AnyLocalizable] = label
        """
        The sample's human-readable short label.
        """
        self.description: Final[AnyLocalizable | None] = description
        """
        The sample's human-readable long description.
        """
        self.size: Final[Size] = size
        """
        The sample size.
        """


@final
class Samples[T]:
    """
    A set of samples.
    """

    def __init__(self, *samples: Callable[[], Sample[T]] | Samples[T]):
        self._samples = tuple(samples)

    def __iter__(self) -> Iterator[Sample[T]]:
        for sample in self._samples:
            if isinstance(sample, Samples):
                yield from sample
            else:
                yield sample()

    def get(self, preferred_size: Size = Size.INTERMEDIATE, /) -> Sample[T]:
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
