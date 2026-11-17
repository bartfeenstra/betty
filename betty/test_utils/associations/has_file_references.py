"""
Test utilities for :py:mod:`betty.associations.has_file_references`.
"""

from __future__ import annotations

from betty.associations.has_file_references import HasFileReferences
from betty.entity import EntityDefinition
from betty.test_utils.locale.localizable import dummy_countable_localizable


@EntityDefinition(
    "dummy-has-file-references",
    label="-",
    label_plural="-",
    label_countable=dummy_countable_localizable,
)
class DummyHasFileReferences(HasFileReferences):
    """
    A dummy :py:class:`betty.associations.has_file_references.HasFileReferences` entity.
    """
