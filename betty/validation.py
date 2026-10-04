"""
The validation API.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Final

from betty.localizer import default_localizer
from betty.user.error import UserFacingError

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, MutableSequence, Sequence

    from betty.localizable import ResolvableLocalizable
    from betty.locator import Locator


type Validator[ValueT, ValidatedT] = Callable[[ValueT], ValidatedT]
"""
A validator.

Validators may return a different value than the ``value`` arg.

:raises: *Invalid
"""


class Invalid(UserFacingError, ValueError):
    """
    Raised when a value is invalid.
    """

    def __init__(
        self,
        message: ResolvableLocalizable,
        *,
        location: Sequence[Locator] = (),
    ):
        super().__init__(
            # Provide a default localization so this exception can be displayed like any other.
            default_localizer.localize(message),
        )
        self.localizable_message: Final[ResolvableLocalizable] = message
        self._location = list(location)

    # @todo Move to HasLocation?
    @property
    def location(self) -> Sequence[Locator]:
        """
        Get the locators describing where the error occurred in the source data.

        The first locator is the innermost, and the last locator is the outermost.
        """
        return self._location

    def locate(self, *locators: Locator) -> None:
        """
        Adds the given locator(s) to the exception.

        The first locator is the innermost, and the last locator is the outermost.
        """
        self._location.extend(locators)


@contextmanager
def locate(*locators: Locator) -> Iterator[None]:
    """
    Re-raise a validation error with the given locators.
    """
    try:
        yield
    except* Invalid as errors:
        for error in errors.exceptions:
            if isinstance(error, Invalid):
                error.locate(*locators)
        raise


@contextmanager
def group[ErrorT: UserFacingError](
    *errors: type[ErrorT],
) -> Iterator[MutableSequence[Invalid | ErrorT]]:
    """
    Reraise all single ``Invalid`` and the given exceptions as exception groups.
    """
    group_ = []
    try:
        # @todo Do we use this group anywhere?
        yield group_
    except (Invalid, *errors) as error:
        group_.append(error)
    finally:
        if group_:
            raise ExceptionGroup(
                "",
                [
                    error if isinstance(error, Invalid) else Invalid(error)
                    for error in group_
                ],
            ) from None
