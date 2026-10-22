"""
The pipeline API.

A pipeline lets you pipe/vent multiple callables into a single callable that takes an input value and returns an output
value. Each pipeline may be (re)used as many times as needed.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from typing import Any, final, override

type Pipe[InputT, OutputT] = Callable[[InputT], OutputT]


class Pipeline[InputT, OutputT](metaclass=ABCMeta):
    """
    A pipeable callable.
    """

    __slots__ = ()

    @abstractmethod
    def __call__(self, value: InputT, /) -> OutputT:
        """
        Invoke the pipeline with a value.
        """

    @final
    def pipe[IntoOutputT](
        self, into: Pipe[OutputT, IntoOutputT], /
    ) -> Pipeline[InputT, IntoOutputT]:
        """
        Return a new pipe consisting of ``self`` with ``into`` added onto it.
        """
        return Inlet(lambda value: into(self(value)))

    __or__ = pipe

    @final
    def vent(self, into: Callable[[OutputT], Any], /) -> Pipeline[InputT, OutputT]:
        """
        Return a new pipe consisting of ``self`` which calls ``into`` but discards its return value.
        """

        def _vent(value: InputT) -> OutputT:
            output = self(value)
            into(output)
            return output

        return Inlet(_vent)

    __truediv__ = vent


@final
class Inlet[InputT, OutputT](Pipeline[InputT, OutputT]):
    """
    Convert a pipeline from the given pipe.
    """

    __slots__ = ("_into",)

    def __init__(self, into: Pipe[InputT, OutputT], /):
        self._into = into

    @override
    def __call__(self, value: InputT, /) -> OutputT:
        return self._into(value)


@final
class Vent[ValueT](Pipeline[ValueT, ValueT]):
    """
    Create a new pipeline that does nothing, but only vents into the given pipe.
    """

    __slots__ = ("_into",)

    def __init__(self, into: Pipe[ValueT, Any], /):
        self._into = into

    @override
    def __call__(self, value: ValueT, /) -> ValueT:
        self._into(value)
        return value


@Inlet
def pipe[T](arg: T, *_: Any, **__: Any) -> T:
    """
    Return the value of the first positional argument.
    """
    return arg
