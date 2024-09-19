"""
Test utilities for :py:mod:`betty.ancestry.description`.
"""

from betty.ancestry.description import HasDescription
from betty.test_utils.ancestry import _LinkedDataObjectSchema


class DummyHasDescription(HasDescription, _LinkedDataObjectSchema):
    """
    A dummy :py:class:`betty.ancestry.description.HasDescription` implementation.
    """

    pass
