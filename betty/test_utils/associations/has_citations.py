"""
Test utilities for :py:mod:`betty.associations.has_citations`.
"""

from __future__ import annotations

from betty.associations.has_citations import HasCitations
from betty.entity import EntityDefinition
from betty.test_utils.locale.localizable import dummy_countable_localizable


@EntityDefinition(
    "dummy-has-citations",
    label="-",
    label_plural="-",
    label_countable=dummy_countable_localizable,
)
class DummyHasCitations(HasCitations):
    """
    A dummy :py:class:`betty.associations.has_citations.HasCitations` entity.
    """
