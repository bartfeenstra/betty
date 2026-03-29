"""
Test utilities for :py:mod:`betty.entity.has_notes`.
"""

from betty.entity import EntityDefinition
from betty.entity.has_notes import HasNotes
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)


@EntityDefinition(
    "dummy-has-notes",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyHasNotes(HasNotes):
    """
    A dummy :py:class:`betty.entity.has_notes.HasNotes` entity.
    """
