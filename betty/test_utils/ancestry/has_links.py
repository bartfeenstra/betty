"""
Test utilities for :py:mod:`betty.entity.has_links`.
"""

from betty.entity import EntityDefinition
from betty.entity.has_links import HasLinks
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
    A dummy :py:class:`betty.entity.has_links.HasLinks` entity.
    """
