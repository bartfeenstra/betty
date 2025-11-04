"""
Provide Gramps error handling utilities.
"""

from betty.exception import HumanFacingException


class GrampsError(Exception):
    """
    A Gramps API error.
    """


class UserFacingGrampsError(GrampsError, HumanFacingException):
    """
    A user-facing Gramps API error.
    """
