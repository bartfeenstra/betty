"""
Test utilities for :py:mod:`betty.associations.has_citations`.
"""

from __future__ import annotations

from betty.associations.has_citations import HasCitations
from betty.entity import EntityDefinition
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
    A dummy :py:class:`betty.associations.has_citations.HasCitations` entity.
    """
