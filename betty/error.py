from betty.locale import DEFAULT_LOCALIZER, Localizable, Localizer


class UserFacingError(Exception, Localizable):
    """
    A localizable, user-facing error.

    This type of error is fatal, but fixing it does not require knowledge of Betty's internals or the stack trace
    leading to the error. It must therefore have an end-user-friendly message, and its stack trace must not be shown.
    """
    def __init__(self, message: Localizable):
        super().__init__(
            # Provide a default localization so this exception can be displayed like any other.
            message.localize(DEFAULT_LOCALIZER),
        )
        self._localizable_message = message

    def __str__(self) -> str:
        return self.localize(DEFAULT_LOCALIZER)

    def localize(self, localizer: Localizer) -> str:
        return self._localizable_message.localize(localizer)
