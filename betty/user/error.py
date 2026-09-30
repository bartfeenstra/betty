"""
User interface errors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.localizable import Localizable, ResolvableLocalizable

if TYPE_CHECKING:
    from betty.localized import LocalizedStr
    from betty.localizer import Localizer


class UserFacingError(Localizable, Exception):
    """
    A user-facing error.

    User interfaces will catch these exceptions as recoverable, and show their localized messages to the user, without
    tracebacks.
    """

    _warn___str__ = False

    def __init__(self, message: ResolvableLocalizable, /):
        super().__init__(
            # We override __str__() to allow for lazy localization.
            ""
        )
        self._user_facing_message = message

    @final
    @override
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        return localizer.localize(self._user_facing_message)
