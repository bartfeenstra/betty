from textwrap import indent
from typing import List


class ContextError(Exception):
    """Define an error with a stack of contextual messages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._contexts: List[str] = []

    def __str__(self):
        return super().__str__() + '\n' + indent('\n'.join(self._contexts), '- ')

    def add_context(self, context: str):
        """
        Add a message describing the error's context.

        Parameters
        ----------
        context: str

        Returns
        -------
        ContextError

        """
        self._contexts.append(context)
        return self


class UserFacingError(Exception):
    """
    Define a user-facing error.

    This type of error is fatal, but fixing it does not require knowledge of Betty's internals or the stack trace
    leading to the error. It must therefore have an end-user-friendly message, and its stack trace must not be shown.
    """

    pass
