"""
Test utilities for :py:mod:`betty.entity.has_citations`.
"""

from betty.entity import EntityDefinition
from betty.entity.has_citations import HasCitations
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
    A dummy :py:class:`betty.entity.has_citations.HasCitations` entity.
    """
