"""
Provide exception handling utilities.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Never, override

from betty.indicator.selector import Selectors
from betty.locale.localizable import Localizable, ResolvableLocalizable
from betty.locale.localize import resolve_localized

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from betty.indicator import Indicator
    from betty.locale import LocalizedStr
    from betty.locale.localize import Localizer


def do_raise(exception: BaseException, /) -> Never:
    """
    Raise the given exception.

    This is helpful as a callback.
    """
    raise exception


@contextmanager
def reraise_with_indicator(*indicators: Indicator) -> Iterator[None]:
    """
    Re-raise a human-facing exception with the given indicators.
    """
    try:
        yield
    except HumanFacingException as error:
        error.with_indicator(*indicators)
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
        indicators: Sequence[Indicator] = (),
    ):
        from betty.locale.localize import default_localizer

        super().__init__(
            # Provide a default localization so this exception can be displayed like any other.
            resolve_localized(message, localizer=default_localizer),
        )
        self._localizable_message = message
        self._indicators = list(indicators)

    @override
    def __str__(self) -> str:
        from betty.locale.localize import default_localizer

        return self.localize(default_localizer)

    @override
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        from betty.locale.localizable.markup import Lines, UnorderedList

        return Lines(
            self._localizable_message,
            UnorderedList(*[
                selector.format()
                for selector in Selectors.reduce(*reversed(self.indicators))
            ]),
        ).localize(localizer)

    @property
    def indicators(self) -> Sequence[Indicator]:
        """
        Get the human-readable indicators describing where the error occurred in the source data.

        The first indicator is the innermost, and the last indicator is the outermost.
        """
        return self._indicators

    def with_indicator(self, *indicators: Indicator) -> None:
        """
        Adds the given indicator(s) to the exception.

        The first indicator is the innermost, and the last indicator is the outermost.
        """
        self._indicators.extend(indicators)
