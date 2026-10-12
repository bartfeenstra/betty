"""
The validation API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from contextlib import AbstractContextManager, contextmanager
from typing import TYPE_CHECKING, Any, Final, Self, final, override

from betty.classtools import abstract
from betty.error import (
    Error,
    ErrorGroup,
    Requires,
    StaticError,
)
from betty.location import HasLocation, ResolvableLocation

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, MutableSequence
    from types import TracebackType

    from betty.localizable import ResolvableLocalizable


type Validator[InputT, OutputT] = Callable[[InputT], OutputT]
"""
A validator.

Validators may return a different value than the ``value`` arg.

:raise Invalid: Raised in case of validation errors with the input value.
"""


@abstract
class Invalid[ValueT](Error, ValueError):
    """
    Raised when a value is invalid.
    """

    def __init__(
        self,
        value: ValueT,
        /,
        *args: Any,
        message: ResolvableLocalizable,
        hint: ResolvableLocalizable | None = None,
        at: ResolvableLocation = (),
        url: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, hint=hint, at=at, message=message, url=url, **kwargs)
        self.value: Final[ValueT] = value
        """
        The invalid value at the time it was invalidated. It may be of a different type or value than was passed on to
        the validator.
        """

    @final
    @override
    def __str__(self) -> str:
        return super().__str__() + "\n\n" + "# Value:\n" + repr(self.value)


@abstract
class StaticInvalid[ValueT](StaticError, Invalid[ValueT]):
    """
    A helper to create :py:class:`betty.validation.Invalid` subclasses.
    """

    def __init__(
        self,
        value: ValueT,
        /,
        *args: Any,
        hint: ResolvableLocalizable | None = None,
        at: ResolvableLocation = (),
        message: ResolvableLocalizable | None = None,
        url: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            value, *args, hint=hint, at=at, message=message, url=url, **kwargs
        )


@final
class InvalidGroup[ValueT](ErrorGroup, StaticInvalid[ValueT]):
    """
    Group one or more validation errors together.
    """

    def __init__(
        self,
        value: ValueT,
        error: Invalid,
        /,
        *errors: Invalid,
        hint: ResolvableLocalizable | None = None,
        message: ResolvableLocalizable | None = None,
        at: ResolvableLocation = (),
        url: ResolvableLocalizable | None = None,
        requires: Requires = Requires.ALL_OF,
    ):
        super().__init__(
            (error, *errors),
            value,
            hint=hint,
            at=at,
            message=message,
            requires=requires,
            url=url,
        )


class _Collector(HasLocation, AbstractContextManager, metaclass=ABCMeta):
    def __init__(self, value: Any, at: ResolvableLocation, requires: Requires, /):
        super().__init__(at=at)
        self._errors: MutableSequence[Invalid] = []
        self._value = value
        self.requires: Final[Requires] = requires

    @final
    def __enter__(self) -> Self:
        return self

    @final
    def add(self, *errors: Invalid) -> None:
        """
        Add one or more errors to the collection.
        """
        self._errors.extend(errors)

    @final
    def clear(self) -> None:
        self._errors.clear()

    @final
    @contextmanager
    def catch(self) -> Generator[None]:
        """
        Catch :py:class:`betty.validation.Invalid` and add it to the error collection.
        """
        try:
            yield
        except Invalid as error:
            self.add(error)

    @final
    def collect(
        self,
        value: Any,
        *,
        at: ResolvableLocation = (),
        requires: Requires = Requires.ALL_OF,
    ) -> _Collector:
        return _NestedCollector(value, self, at, requires)

    @final
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        if self._errors:
            self._finish(
                InvalidGroup(
                    self._value,
                    *self._errors,
                    at=self._at,
                    requires=self.requires,
                )
            )
            self.clear()

    @abstractmethod
    def _finish(self, error: InvalidGroup, /) -> None:
        pass


@final
class _RootCollector(_Collector):
    @override
    def _finish(self, error: InvalidGroup, /) -> None:
        raise error


@final
class _NestedCollector(_Collector):
    def __init__(
        self,
        value: Any,
        parent: _Collector,
        at: ResolvableLocation,
        requires: Requires,
    ):
        super().__init__(value, at, requires)
        self._parent = parent

    @override
    def _finish(self, error: InvalidGroup, /) -> None:
        self._parent.add(error)


def collect(
    value: Any, /, *, at: ResolvableLocation = (), requires: Requires = Requires.ALL_OF
) -> _RootCollector:
    """
    Collect errors before raising them as an :py:class:`betty.validation.InvalidGroup`.
    """
    return _RootCollector(value, at, requires)
