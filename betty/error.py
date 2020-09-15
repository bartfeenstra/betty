from textwrap import indent
from typing import List


class ExternalContextError(Exception):

    """
    An error depending on Betty's external context, e.g. not caused by internal failure.

    This type of error is fatal, but fixing it does not require knowledge of Betty's internals or the stack trace
    leading to the error. Instead, the error message must provide contextual information, and the error may be caught,
    its description extended using wrap(), and re-raised.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._contexts: List[str] = []

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
