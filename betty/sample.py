"""
Samples are used to generate documentation about various parts of Betty.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum, auto
from typing import TYPE_CHECKING, Generic, Self, TypeVar, final

from betty.locale.localizable import resolve_localizable

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from betty.locale.localizable import Localizable, ResolvableLocalizable
    from betty.typing import Intersection


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
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        size: Size = Size.INTERMEDIATE,
    ):
        self._subject = subject
        self._label = resolve_localizable(label)
        self._description = resolve_localizable(description) if description else None
        self._size = size

    @property
    def subject(self) -> T:
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


_SampleT = TypeVar("_SampleT", covariant=True)


@final
class Samples(
    Generic[_SampleT],  # noqa: UP046
):
    """
    A set of samples.
    """

    def __init__(
        self,
        samples: Iterable[
            Callable[[], Sample[_SampleT]]
            | Samples[_SampleT]
            | type[Intersection[_SampleT, Samplable]]
        ],
    ):
        self._samples = list(samples)

    def __iter__(self) -> Iterator[Sample[_SampleT]]:
        for sample in self._samples:
            if isinstance(sample, Samples):
                yield from sample
            elif isinstance(sample, type) and issubclass(sample, Samplable):
                yield from sample.samples()  # ty:ignore[invalid-yield]
            else:
                yield sample()

    def get(self, preferred_size: Size = Size.INTERMEDIATE, /) -> Sample[_SampleT]:
        """
        Get a sample.
        """
        samples = sorted(self, key=lambda sample: abs(preferred_size - sample.size))
        if samples:
            return samples[0]
        raise SampleNotFound


class Samplable(ABC):
    """
    Allow a class to provide its own samples.
    """

    @classmethod
    @abstractmethod
    def samples(cls) -> Samples[Self]:
        """
        Get the samples.
        """


class SampleNotFound(Exception):
    """
    Raised when a sample could not be found.
    """
