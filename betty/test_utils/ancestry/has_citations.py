"""
Test utilities for :py:mod:`betty.ancestry.has_citations`.
"""

from betty.ancestry.has_citations import HasCitations
from betty.model import EntityDefinition
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)


@EntityDefinition(
    "dummy-has-citations",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyHasCitations(HasCitations):
    """
    A dummy :py:class:`betty.ancestry.has_citations.HasCitations` entity.
    """
