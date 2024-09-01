"""
Provide Gramps error handling utilities.
"""

from betty.error import UserFacingError


class GrampsError(Exception):
    """
    A Gramps API error.
    """

    pass  # pragma: no cover


class UserFacingGrampsError(GrampsError, UserFacingError):
    """
    A user-facing Gramps API error.
    """

    pass  # pragma: no cover
