"""
Provide Gramps error handling utilities.
"""

from betty.exception import UserFacingException


class GrampsError(Exception):
    """
    A Gramps API error.
    """


class UserFacingGrampsError(GrampsError, UserFacingException):
    """
    A user-facing Gramps API error.
    """
