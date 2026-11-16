"""
Test utilities for :py:mod:`betty.associations.has_links`.
"""

from __future__ import annotations

from betty.associations.has_links import HasLinks
from betty.entity import EntityDefinition
from betty.test_utils.locale.localizable import dummy_countable_localizable


@EntityDefinition(
    "dummy-has-links",
    label="-",
    label_plural="-",
    label_countable=dummy_countable_localizable,
)
class DummyHasLinks(HasLinks):
    """
    A dummy :py:class:`betty.associations.has_links.HasLinks` entity.
    """
