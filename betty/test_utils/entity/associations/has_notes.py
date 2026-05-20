"""
Test utilities for :py:mod:`betty.associations.has_notes`.
"""

from __future__ import annotations

from betty.associations.has_notes import HasNotes
from betty.entity import EntityDefinition
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
)


@EntityDefinition(
    "dummy-has-notes",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyHasNotes(HasNotes):
    """
    A dummy :py:class:`betty.associations.has_notes.HasNotes` entity.
    """
