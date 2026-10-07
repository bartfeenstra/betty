"""
Error handling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, final, override

from betty.localizable import Localizable, ResolvableLocalizable
from betty.localizer import Localizer, default_localizer
from betty.user.location import HasLocation, Locator

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.localized import LocalizedStr


class UserFacingError(HasLocation, Localizable, Exception):
    """
    An exception that is user-facing and may be presented to the user as a regular error, without traceback.
    """

    def __init__(
        self,
        message: ResolvableLocalizable,
        *args: Any,
        hint: ResolvableLocalizable | None = None,
        location: Iterable[Locator] = (),
        url: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, location=location, **kwargs)
        self.message: Final[ResolvableLocalizable] = message
        self.hint: Final[ResolvableLocalizable | None] = hint
        self.url: Final[ResolvableLocalizable | None] = url

    @final
    @override
    def __str__(self) -> str:
        message_str = default_localizer.localize(self.message)
        # @todo Show the location...
        if self.hint:
            message_str += "\n\nHint\n----" + default_localizer.localize(self.hint)
        if self.url:
            message_str += (
                "\n\nDocumentation\n-------------"
                + default_localizer.localize(self.url)
            )
        return message_str

    @final
    @override
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        return localizer.localize(self.message)

    def locate(self, *location: Locator) -> None:
        """
        Add the given locator(s) to the error.

        The first locator is the innermost, and the last locator is the outermost.
        """
        self._location = (*self._location, *location)
