"""
The validation API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from contextlib import AbstractContextManager, contextmanager
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar, Final, Self, final, override

from betty.localizables.gettext import _
from betty.user.error import UserFacingError
from betty.user.location import HasLocation

if TYPE_CHECKING:
    from collections.abc import (
        Callable,
        Generator,
        Iterable,
        Iterator,
        Mapping,
        MutableSequence,
    )
    from types import TracebackType

    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.user.location import Locator


type Validator[InputT, OutputT] = Callable[[InputT], OutputT]
"""
A validator.

Validators may return a different value than the ``value`` arg.

:raise Invalid: Raised in case of validation errors with the input value.
"""


class Invalid[ValueT = Any](UserFacingError, ValueError):
    """
    Raised when a value is invalid.
    """

    def __init__(
        self,
        value: ValueT,
        message: ResolvableLocalizable,
        /,
        *args: Any,
        location: Iterable[Locator] = (),
        **kwargs: Any,
    ):
        super().__init__(message, *args, location=location, **kwargs)
        self.value: Final[ValueT] = value
        """
        The invalid value at the time it was invalidated. It may be of a different type or value than was passed on to
        the validator.
        """


@final
class InvalidGroup[ValueT](Invalid[ValueT]):
    """
    Group one or more errors together.
    """

    @final
    class Rel(Enum):
        """
        An error group relationship.

        When grouping errors, the relationship indicates whether one, any, or all of the errors must be addressed for
        validation to pass.
        """

        ONE = "one"
        ANY = "any"
        ALL = "all"

    _messages: ClassVar[Mapping[Rel, Localizable]] = {
        Rel.ONE: _("One of the problems must be fixed."),
        Rel.ANY: _("At least one of the problems must be fixed."),
        Rel.ALL: _("All of the problems must be fixed."),
    }

    def __init__(
        self,
        value: ValueT,
        error: Invalid,
        *errors: Invalid,
        location: Iterable[Locator] = (),
        rel: Rel = Rel.ALL,
    ):
        errors = (error, *errors)
        super().__init__(value, self._messages[rel], location=location)
        self._errors = errors
        for error_ in errors:
            error_.locate(*location)
        self.rel: Final[InvalidGroup.Rel] = rel
        """
        The relationship between the errors.
        """

    def __iter__(self) -> Iterator[Invalid]:
        return iter(self._errors)

    def __getitem__(self, index: int, /) -> Invalid:
        return self._errors[index]

    @override
    def locate(self, *location: Locator) -> None:
        super().locate(*location)
        for error in self:
            error.locate(*location)


class _Collector(HasLocation, AbstractContextManager, metaclass=ABCMeta):
    def __init__(
        self, value: Any, location: Iterable[Locator], rel: InvalidGroup.Rel, /
    ):
        super().__init__(location=location)
        self._errors: MutableSequence[Invalid] = []
        self._value = value
        self.rel: Final[InvalidGroup.Rel] = rel

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
        location: Iterable[Locator] = (),
        rel: InvalidGroup.Rel = InvalidGroup.Rel.ALL,
    ) -> _Collector:
        return _NestedCollector(value, self, location, rel)

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
                    self._value, *self._errors, location=self._location, rel=self.rel
                )
            )
            self.clear()

    @abstractmethod
    def _finish(self, errors: InvalidGroup, /) -> None:
        pass


@final
class _RootCollector(_Collector):
    @override
    def _finish(self, errors: InvalidGroup, /) -> None:
        raise errors


@final
class _NestedCollector(_Collector):
    def __init__(
        self,
        value: Any,
        parent: _Collector,
        location: Iterable[Locator],
        rel: InvalidGroup.Rel,
    ):
        super().__init__(value, location, rel)
        self._parent = parent

    @override
    def _finish(self, errors: InvalidGroup, /) -> None:
        self._parent.add(errors)


def collect(
    value: Any,
    *,
    location: Iterable[Locator] = (),
    rel: InvalidGroup.Rel = InvalidGroup.Rel.ALL,
) -> _RootCollector:
    """
    Collect errors before raising them as an :py:class:`betty.validation.InvalidGroup`.
    """
    return _RootCollector(value, location, rel)
