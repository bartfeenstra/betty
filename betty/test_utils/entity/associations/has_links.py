"""
Test utilities for :py:mod:`betty.associations.has_links`.
"""

from __future__ import annotations

from betty.associations.has_links import HasLinks
from betty.entity import EntityDefinition
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
)


@EntityDefinition(
    "dummy-has-links",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyHasLinks(HasLinks):
    """
    A dummy :py:class:`betty.associations.has_links.HasLinks` entity.
    """
