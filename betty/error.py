class UserFacingError(Exception):
    """
    A user-facing error.

    This type of error is fatal, but fixing it does not require knowledge of Betty's internals or the stack trace
    leading to the error. It must therefore have an end-user-friendly message, and its stack trace must not be shown.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
