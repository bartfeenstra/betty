"""
Test utilities for :py:mod:`betty.ancestry.privacy`.
"""

from betty.ancestry.privacy import HasPrivacy
from betty.test_utils.ancestry import _LinkedDataObjectSchema


class DummyHasPrivacy(HasPrivacy, _LinkedDataObjectSchema):
    """
    A dummy :py:class:`betty.ancestry.privacy.HasPrivacy` implementation.
    """

    pass
