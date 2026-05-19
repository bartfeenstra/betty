"""
Test utilities for :py:mod:`betty.entity.has_citations`.
"""

from betty.entity import EntityDefinition
from betty.entity.has_citations import HasCitations
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
)


@EntityDefinition(
    "dummy-has-citations",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyHasCitations(HasCitations):
    """
    A dummy :py:class:`betty.entity.has_citations.HasCitations` entity.
    """
