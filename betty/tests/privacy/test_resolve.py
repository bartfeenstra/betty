from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.privacy import (
    Privacy,
)
from betty.privacy.resolve import (
    is_private,
    is_public,
    merge_privacies,
    merge_secondary_privacies,
    resolve_privacy,
)
from betty.test_utils.privacy import DummyHasPrivacy

if TYPE_CHECKING:
    from betty.attrs.privacy import HasPrivacy


@pytest.mark.parametrize(
    ("expected", "target"),
    [
        (True, DummyHasPrivacy(privacy=Privacy.PRIVATE)),
        (False, DummyHasPrivacy(privacy=Privacy.PUBLIC)),
        (False, DummyHasPrivacy(privacy=Privacy.UNDETERMINED)),
        (False, object()),
    ],
)
def test_is_private(expected: bool, target: Any) -> None:
    assert expected == is_private(target)


@pytest.mark.parametrize(
    ("expected", "target"),
    [
        (False, DummyHasPrivacy(privacy=Privacy.PRIVATE)),
        (True, DummyHasPrivacy(privacy=Privacy.PUBLIC)),
        (True, DummyHasPrivacy(privacy=Privacy.UNDETERMINED)),
        (True, object()),
    ],
)
def test_is_public(expected: bool, target: Any) -> None:
    assert expected == is_public(target)


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
def test_resolve_privacy(expected: Privacy, privacy: Privacy | HasPrivacy) -> None:
    assert resolve_privacy(privacy) == expected


@pytest.mark.parametrize(
    ("expected", "privacies"),
    [
        (Privacy.PUBLIC, (Privacy.PUBLIC,)),
        (Privacy.UNDETERMINED, (Privacy.UNDETERMINED,)),
        (Privacy.PRIVATE, (Privacy.PRIVATE,)),
        (Privacy.UNDETERMINED, (Privacy.PUBLIC, Privacy.UNDETERMINED)),
        (Privacy.PRIVATE, (Privacy.PUBLIC, Privacy.PRIVATE)),
        (Privacy.PRIVATE, (Privacy.UNDETERMINED, Privacy.PRIVATE)),
        (Privacy.PRIVATE, (Privacy.PUBLIC, Privacy.UNDETERMINED, Privacy.PRIVATE)),
    ],
)
def test_merge_privacies(expected: Privacy, privacies: tuple[Privacy]) -> None:
    assert expected == merge_privacies(*privacies)


@pytest.mark.parametrize(
    ("expected", "privacies"),
    [
        (Privacy.PUBLIC, (Privacy.PUBLIC,)),
        (Privacy.UNDETERMINED, (Privacy.UNDETERMINED,)),
        (Privacy.PRIVATE, (Privacy.PRIVATE,)),
        (Privacy.PUBLIC, (Privacy.PUBLIC, Privacy.UNDETERMINED)),
        (Privacy.PRIVATE, (Privacy.PUBLIC, Privacy.PRIVATE)),
        (Privacy.PRIVATE, (Privacy.UNDETERMINED, Privacy.PRIVATE)),
        (Privacy.PRIVATE, (Privacy.PUBLIC, Privacy.UNDETERMINED, Privacy.PRIVATE)),
    ],
)
def test_merge_secondary_privacies(
    expected: Privacy, privacies: tuple[Privacy]
) -> None:
    assert expected == merge_secondary_privacies(*privacies)
