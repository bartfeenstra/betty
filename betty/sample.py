"""
Samples are used to generate documentation about various parts of Betty.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from enum import IntEnum, auto
from typing import TYPE_CHECKING, Final, Generic, Self, TypeVar, final

from betty.localizable import resolve_localizable

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from ty_extensions import Intersection

    from betty.localizable import Localizable, ResolvableLocalizable


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
        self.subject: Final[T] = subject
        """
        The sample subject.
        """
        self.label: Final[Localizable] = resolve_localizable(label)
        """
        The sample's human-readable short label.
        """
        self.description: Final[Localizable | None] = (
            resolve_localizable(description) if description else None
        )
        """
        The sample's human-readable long description.
        """
        self.size: Final[Size] = size
        """
        The sample size.
        """


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


class Samplable(metaclass=ABCMeta):
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
