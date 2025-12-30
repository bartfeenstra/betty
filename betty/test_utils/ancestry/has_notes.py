"""
Test utilities for :py:mod:`betty.ancestry.has_notes`.
"""

from betty.ancestry.has_notes import HasNotes
from betty.model import EntityDefinition
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
    A dummy :py:class:`betty.ancestry.has_notes.HasNotes` entity.
    """
