"""
Optional data types for when ``None`` is not sufficient.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Never, Self, final

if TYPE_CHECKING:
    from collections.abc import Callable


@final
class IsNothing(ValueError):
    """
    Raise when performing operations on :py:class:`betty.maybe.Nothing`.
    """

    def __init__(self):
        super().__init__(f"This <{Maybe.__name__}> value is {repr(Nothing)}.")


@final
class Something[SomethingT]:
    """
    A maybe value.
    """

    __slots__ = ("_something",)

    def __init__(self, something: SomethingT, /):
        self._something = something

    @property
    def something(self) -> SomethingT:
        """
        The something value.
        """
        return self._something

    def __call__(self) -> SomethingT:
        """
        Get the something value.
        """
        return self.something

    def map[NewSomethingT](
        self, function: Callable[[SomethingT], Maybe[NewSomethingT]], /
    ) -> Maybe[NewSomethingT]:
        """
        Apply a function to the value, and return its result.
        """
        return function(self._something)

    __or__ = map  # noqa: A003

    def map_from[NewSomethingT](
        self, function: Callable[[SomethingT], NewSomethingT], /
    ) -> Something[NewSomethingT]:
        """
        Apply a function to the value, and return its result wrapped in :py:class:`betty.maybe.Something`.
        """
        return Something(function(self._something))

    __ior__ = map_from

    def map_nothing(self, _: Callable[[], Maybe[Any]], /) -> Self:
        """
        Apply a function to the nothing, and return its result.
        """
        return self

    __xor__ = map_nothing

    def map_nothing_from(self, _: Callable[[], Any], /) -> Self:
        """
        Apply a function to the nothing, and return its result wrapped in :py:class:`betty.maybe.Something`.
        """
        return self

    __ixor__ = map_nothing_from

    def __repr__(self):
        return f"<{type(self).__name__}: {repr(self._something)}>"


class _NothingMeta(type):
    @property
    def something(self) -> Never:
        """
        The something value.

        :raises IsNothing: Always raised because the value is :py:class:`betty.maybe.Nothing`.
        """
        raise IsNothing

    def __call__(cls) -> Never:
        """
        Get the maybe value.

        :raises IsNothing: Always raised because the value is :py:class:`betty.maybe.Nothing`.
        """
        raise IsNothing

    def map(cls, _: Callable[[Any], Maybe[Any]], /) -> NothingType:
        """
        Apply a function to the value, and return its result.
        """
        return Nothing

    __or__ = map  # noqa: A003

    def map_from(cls, _: Callable[[Any], Any], /) -> NothingType:
        """
        Apply a function to the value, and return its result wrapped in :py:class:`betty.maybe.Something`.
        """
        return Nothing

    __ior__ = map_from

    def map_nothing[NewSomethingT](
        self, function: Callable[[], Maybe[NewSomethingT]], /
    ) -> Maybe[NewSomethingT]:
        """
        Apply a function to the nothing, and return its result.
        """
        return function()

    __xor__ = map_nothing

    def map_nothing_from[NewSomethingT](
        self, function: Callable[[], NewSomethingT], /
    ) -> Something[NewSomethingT]:
        """
        Apply a function to the nothing, and return its result wrapped in :py:class:`betty.maybe.Something`.
        """
        return Something(function())

    __ixor__ = map_nothing_from

    def __repr__(cls):
        return f"<{Nothing.__name__}>"


@final
class Nothing(metaclass=_NothingMeta):
    """
    A missing maybe value.
    """

    def __new__(cls):  # noqa: D102
        raise TypeError(f"{cls.__name__} cannot be initialized.")


type NothingType = type[Nothing]

type Maybe[SomethingT] = Something[SomethingT] | NothingType
