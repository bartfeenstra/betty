"""
Test utilities for :py:mod:`betty.ancestry.date`.
"""

from betty.ancestry.date import HasDate
from betty.test_utils.ancestry import _LinkedDataObjectSchema


class DummyHasDate(HasDate, _LinkedDataObjectSchema):
    """
    A dummy :py:class:`betty.ancestry.date.HasDate` implementation.
    """

    pass
