"""
Test utilities for :py:mod:`betty.ancestry.locale`.
"""

from betty.ancestry.locale import HasLocale
from betty.test_utils.ancestry import _LinkedDataObjectSchema


class DummyHasLocale(HasLocale, _LinkedDataObjectSchema):
    """
    A dummy :py:class:`betty.ancestry.locale.HasLocale` implementation.
    """

    pass
