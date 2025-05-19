"""
Provide exception handling utilities.
"""

from typing import Never

from typing_extensions import override

from betty.locale.localizable import Localizable
from betty.locale.localized import LocalizedStr
from betty.locale.localizer import Localizer
from betty.user import UserFacing


def do_raise(exception: BaseException) -> Never:
    """
    Raise the given exception.

    This is helpful as a callback.
    """
    raise exception


class UserFacingException(Exception, Localizable, UserFacing):
    """
    A localizable, user-facing exception.

    When encountering an exception that extends this base class, Betty will show the localized exception message, and
    no stack trace.
    """

    def __init__(self, message: Localizable):
        from betty.locale.localizer import DEFAULT_LOCALIZER

        super().__init__(
            # Provide a default localization so this exception can be displayed like any other.
            message.localize(DEFAULT_LOCALIZER),
        )
        self._localizable_message = message

    @override
    def __str__(self) -> str:
        from betty.locale.localizer import DEFAULT_LOCALIZER

        return self.localize(DEFAULT_LOCALIZER)

    @override
    def localize(self, localizer: Localizer) -> LocalizedStr:
        return self._localizable_message.localize(localizer)
