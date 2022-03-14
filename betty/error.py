from contextlib import contextmanager
from textwrap import indent
from typing import List, Optional, Iterator


class ContextError(Exception):

    """
    An error with a stack of contextual messages.
    """

    def __init__(self, *args, contexts: Optional[List[str]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._contexts: List[str] = [] if contexts is None else contexts

    def __str__(self):
        return super().__str__() + '\n' + indent('\n'.join(self._contexts), '- ')

    def add_context(self, context: str):
        """
        Add a message describing the error's context.

        :param context: str
        :return: ExternalContextError
        """
        self._contexts.append(context)
        return self


@contextmanager
def ensure_context(*contexts: str) -> Iterator[None]:
    try:
        yield
    except ContextError as e:
        for context in contexts:
            e.add_context(context)
        raise


class UserFacingError(Exception):
    """
    A user-facing error.

    This type of error is fatal, but fixing it does not require knowledge of Betty's internals or the stack trace
    leading to the error. It must therefore have an end-user-friendly message, and its stack trace must not be shown.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
