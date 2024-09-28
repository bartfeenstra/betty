"""
Test utilities for :py:mod:`betty.privacy`.
"""

from betty.privacy import HasPrivacy
from betty.test_utils.ancestry import _LinkedDataObjectSchema


class DummyHasPrivacy(HasPrivacy, _LinkedDataObjectSchema):
    """
    A dummy :py:class:`betty.privacy.HasPrivacy` implementation.
    """

    pass
