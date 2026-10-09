"""
Length validators.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Sized
from typing import TYPE_CHECKING, Final, final, overload, override

from betty.functools import Pipe
from betty.localizables.gettext import _
from betty.validation import Invalid

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable
    from betty.user.location import Locator


class _InvalidLength[ValueT: Sized](Invalid[ValueT]):
    def __init__(
        self,
        value: ValueT,
        message: ResolvableLocalizable,
        min_len: int | None,
        max_len: int | None,
        /,
        *,
        location: Iterable[Locator] = (),
    ):
        super().__init__(value, location=location, message=message)
        self.min_len: Final[int | None] = min_len
        self.max_len: Final[int | None] = max_len


@final
class TooShort(_InvalidLength):
    """
    Raised when a value is too short.
    """


@final
class TooLong(_InvalidLength):
    """
    Raised when a value is too long.
    """


class _IsLen[ValueT: Sized](metaclass=ABCMeta):
    @overload
    def __call__(self, expected: int, /) -> Pipe[ValueT, ValueT]:
        pass

    @overload
    def __call__(self, value: ValueT, expected: int, /) -> ValueT:
        pass

    def __call__(self, *args):
        """
        Validate the value's length.
        """
        if len(args) == 2:
            return self._validate(*args)
        return Pipe(lambda value: self._validate(value, *args))

    @abstractmethod
    def _validate(self, value: ValueT, expected: int, /) -> ValueT:
        pass


@final
class IsLen[ValueT: Sized](_IsLen[ValueT]):
    """
    Validate the exact length of :py:class:`collections.abc.Sized` values.
    """

    def __init__(self, message: ResolvableLocalizable, /):
        self._message = message

    @override
    def _validate(self, value: ValueT, expected: int, /) -> ValueT:
        actual = len(value)
        if actual < expected:
            raise TooShort(value, self._message, expected, expected)
        if actual > expected:
            raise TooLong(value, self._message, expected, expected)
        return value


@final
class IsMinLen[ValueT: Sized](_IsLen[ValueT]):
    """
    Validate the minimum length of :py:class:`collections.abc.Sized` values.
    """

    def __init__(self, message: ResolvableLocalizable, /):
        self._message = message

    @override
    def _validate(self, value: ValueT, expected: int, /) -> ValueT:
        if len(value) < expected:
            raise TooShort(value, self._message, expected, None)
        return value


@final
class IsMaxLen[ValueT: Sized](_IsLen[ValueT]):
    """
    Validate the maximum length of :py:class:`collections.abc.Sized` values.
    """

    def __init__(self, message: ResolvableLocalizable, /):
        self._message = message

    @override
    def _validate(self, value: ValueT, expected: int, /) -> ValueT:
        if len(value) > expected:
            raise TooLong(value, self._message, None, expected)
        return value


is_len = IsLen(_("This must have a length of {length}."))
is_min_len = IsMinLen(_("This must have a length of at least {length}."))
is_max_len = IsMaxLen(_("This must have a length of at most {length}."))
