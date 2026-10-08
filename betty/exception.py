"""
Provide exception handling utilities.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Never, override

from betty.localizable import Localizable, ResolvableLocalizable
from betty.localizables.markup import Lines, UnorderedList
from betty.localizer import default_localizer
from betty.user.location import format_, reduce

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from betty.localized import LocalizedStr
    from betty.localizer import Localizer
    from betty.user.location import Locator


def do_raise(exception: BaseException, /) -> Never:
    """
    Raise the given exception.

    This is helpful as a callback.
    """
    raise exception


@contextmanager
def reraise_with_locator(*locators: Locator) -> Generator[None]:
    """
    Re-raise a human-facing exception with the given locators.
    """
    try:
        yield
    except HumanFacingException as error:
        error.with_locator(*locators)
        raise


class HumanFacingException(Exception, Localizable):
    """
    A localizable, human-facing exception.

    When encountering an exception that extends this base class, Betty will show the localized exception message, and
    no stack trace.
    """

    def __init__(
        self,
        message: ResolvableLocalizable,
        *,
        locators: Sequence[Locator] = (),
    ):
        super().__init__(
            # Provide a default localization so this exception can be displayed like any other.
            default_localizer.localize(message),
        )
        self._localizable_message = message
        self._locators = list(locators)

    @override
    def __str__(self) -> str:
        return self.localize(default_localizer)

    @override
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        return Lines(
            self._localizable_message,
            UnorderedList(
                *format_(*reduce(*reversed(self.locators)), localizer=localizer)
            ),
        ).localize(localizer)

    @property
    def locators(self) -> Sequence[Locator]:
        """
        Get the human-readable locators describing where the error occurred in the source data.

        The first locator is the innermost, and the last locator is the outermost.
        """
        return self._locators

    def with_locator(self, *locators: Locator) -> None:
        """
        Adds the given locator(s) to the exception.

        The first locator is the innermost, and the last locator is the outermost.
        """
        self._locators.extend(locators)
