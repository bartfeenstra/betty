from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.privacy import Privacy, merge_privacies, override_privacies, resolve_privacy
from betty.test_utils.privacy import DummyHasPrivacy

if TYPE_CHECKING:
    from betty.privacy import ResolvablePrivacy


@pytest.mark.parametrize(
    ("expected", "privacy"),
    [
        (Privacy.PUBLIC, Privacy.PUBLIC),
        (Privacy.PRIVATE, Privacy.PRIVATE),
        (Privacy.UNDETERMINED, Privacy.UNDETERMINED),
        (Privacy.PUBLIC, DummyHasPrivacy(privacy=Privacy.PUBLIC)),
        (Privacy.PRIVATE, DummyHasPrivacy(privacy=Privacy.PRIVATE)),
        (Privacy.UNDETERMINED, DummyHasPrivacy(privacy=Privacy.UNDETERMINED)),
    ],
)
def test_resolve_privacy(expected: Privacy, privacy: ResolvablePrivacy) -> None:
    assert resolve_privacy(privacy) == expected


@pytest.mark.parametrize(
    ("expected", "privacies"),
    [
        (Privacy.UNDETERMINED, []),
        (Privacy.UNDETERMINED, [Privacy.UNDETERMINED]),
        (Privacy.PUBLIC, [Privacy.PUBLIC]),
        (Privacy.PRIVATE, [Privacy.PRIVATE]),
        (Privacy.UNDETERMINED, [Privacy.UNDETERMINED, Privacy.UNDETERMINED]),
        (Privacy.PUBLIC, [Privacy.PUBLIC, Privacy.UNDETERMINED]),
        (Privacy.PRIVATE, [Privacy.PRIVATE, Privacy.UNDETERMINED]),
        (Privacy.PUBLIC, [Privacy.UNDETERMINED, Privacy.PUBLIC]),
        (Privacy.PUBLIC, [Privacy.PUBLIC, Privacy.PUBLIC]),
        (Privacy.PRIVATE, [Privacy.PRIVATE, Privacy.PUBLIC]),
        (Privacy.PRIVATE, [Privacy.UNDETERMINED, Privacy.PRIVATE]),
        (Privacy.PRIVATE, [Privacy.PUBLIC, Privacy.PRIVATE]),
        (Privacy.PRIVATE, [Privacy.PRIVATE, Privacy.PRIVATE]),
    ],
)
def test_merge_privacies(expected: Privacy, privacies: tuple[Privacy]) -> None:
    assert merge_privacies(*privacies) == expected


@pytest.mark.parametrize(
    ("expected", "privacies"),
    [
        (Privacy.UNDETERMINED, []),
        (Privacy.UNDETERMINED, [Privacy.UNDETERMINED]),
        (Privacy.UNDETERMINED, [Privacy.UNDETERMINED, Privacy.UNDETERMINED]),
        (Privacy.PUBLIC, [Privacy.UNDETERMINED, Privacy.PUBLIC]),
        (Privacy.PRIVATE, [Privacy.UNDETERMINED, Privacy.PRIVATE]),
        (Privacy.PUBLIC, [Privacy.PUBLIC]),
        (Privacy.PUBLIC, [Privacy.PUBLIC, Privacy.UNDETERMINED]),
        (Privacy.PUBLIC, [Privacy.PUBLIC, Privacy.PUBLIC]),
        (Privacy.PUBLIC, [Privacy.PUBLIC, Privacy.PRIVATE]),
        (Privacy.PRIVATE, [Privacy.PRIVATE]),
        (Privacy.PRIVATE, [Privacy.PRIVATE, Privacy.UNDETERMINED]),
        (Privacy.PRIVATE, [Privacy.PRIVATE, Privacy.PUBLIC]),
        (Privacy.PRIVATE, [Privacy.PRIVATE, Privacy.PRIVATE]),
    ],
)
def test_override_privacies(expected: Privacy, privacies: tuple[Privacy]) -> None:
    assert override_privacies(*privacies) == expected
