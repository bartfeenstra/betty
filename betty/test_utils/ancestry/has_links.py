"""
Test utilities for :py:mod:`betty.ancestry.has_links`.
"""

from betty.ancestry.has_links import HasLinks
from betty.model import EntityDefinition
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)


@EntityDefinition(
    "dummy-has-links",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyHasLinks(HasLinks):
    """
    A dummy :py:class:`betty.ancestry.has_links.HasLinks` entity.
    """
