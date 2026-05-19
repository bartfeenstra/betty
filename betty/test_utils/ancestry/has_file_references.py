"""
Test utilities for :py:mod:`betty.entity.has_file_references`.
"""

from betty.entity import EntityDefinition
from betty.entity.has_file_references import HasFileReferences
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
)


@EntityDefinition(
    "dummy-has-file-references",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyHasFileReferences(HasFileReferences):
    """
    A dummy :py:class:`betty.entity.has_file_references.HasFileReferences` entity.
    """
