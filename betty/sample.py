"""
Samples are used to generate documentation about various parts of Betty.
"""

from __future__ import annotations

from enum import IntEnum, auto
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

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
class Sample[SampleT]:
    """
    A sample.

    Samples are useful for generating documentation and tests.
    """

    def __init__(
        self,
        subject: Callable[[], SampleT],
        *,
        label: AnyLocalizable,
        description: AnyLocalizable | None = None,
        size: Size = Size.INTERMEDIATE,
    ):
        self._subject = subject
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

    @property
    def subject(self) -> SampleT:
        """
        The sample subject.
        """
        return self._subject()


type ResolvableSamples[SampleT] = (
    Samples[SampleT] | tuple[Sample[SampleT], ...] | Sample[SampleT]
)


def _resolve_samples[SampleT](
    *samples: ResolvableSamples[SampleT],
) -> Iterable[Sample[SampleT]]:
    for samples_ in samples:
        if isinstance(samples_, Sample):
            yield samples_
        else:
            yield from samples_


@final
class Samples[SampleT]:
    """
    A set of samples.
    """

    def __init__(self, *samples: ResolvableSamples[SampleT]):
        self._samples = tuple(map(_resolve_samples, samples))

    def __iter__(self) -> Iterator[Sample[SampleT]]:
        return iter(self._samples)

    def get(self, preferred_size: Size = Size.INTERMEDIATE, /) -> Sample[SampleT]:
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
