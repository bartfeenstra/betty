from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.privacy import (
    HasPrivacy,
    Privacy,
    is_private,
    is_public,
    merge_privacies,
    merge_secondary_privacies,
    resolve_privacy,
)
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.privacy import DummyHasPrivacy

if TYPE_CHECKING:
    from betty.serde import SerializedData, SerializedMapping


class TestHasPrivacy:
    @pytest.mark.parametrize(
        ("expected", "privacy"),
        [
            (Privacy.UNDETERMINED, Privacy.UNDETERMINED),
            (Privacy.PUBLIC, Privacy.PUBLIC),
            (Privacy.PRIVATE, Privacy.PRIVATE),
        ],
    )
    async def test___init__(
        self,
        expected: Privacy,
        privacy: Privacy | None,
    ) -> None:
        sut = DummyHasPrivacy(privacy=privacy)
        assert sut.privacy is expected

    async def test_privacy(self) -> None:
        sut = DummyHasPrivacy()
        privacy = Privacy.PUBLIC
        sut.privacy = privacy
        assert sut.privacy is privacy
        del sut.privacy
        assert sut.privacy is Privacy.UNDETERMINED

    async def test_own_privacy(self) -> None:
        sut = DummyHasPrivacy()
        privacy = Privacy.PUBLIC
        sut.privacy = privacy
        assert sut.own_privacy is privacy

    async def test_public(self) -> None:
        sut = DummyHasPrivacy()
        sut.public = True
        assert sut.public
        assert sut.privacy is Privacy.PUBLIC

    async def test_private(self) -> None:
        sut = DummyHasPrivacy()
        sut.private = True
        assert sut.private
        assert sut.privacy is Privacy.PRIVATE

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {
                    "private": True,
                },
                DummyHasPrivacy(privacy=Privacy.PRIVATE),
            ),
            (
                {
                    "private": False,
                },
                DummyHasPrivacy(privacy=Privacy.PUBLIC),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: SerializedMapping[SerializedData], sut: HasPrivacy
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected


@pytest.mark.parametrize(
    ("expected", "target"),
    [
        (True, DummyHasPrivacy(privacy=Privacy.PRIVATE)),
        (False, DummyHasPrivacy(privacy=Privacy.PUBLIC)),
        (False, DummyHasPrivacy(privacy=Privacy.UNDETERMINED)),
        (False, object()),
    ],
)
async def test_is_private(expected: bool, target: Any) -> None:
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
async def test_is_public(expected: bool, target: Any) -> None:
    assert expected == is_public(target)


@pytest.mark.parametrize(
    ("expected", "privacy"),
    [
        (Privacy.PUBLIC, Privacy.PUBLIC),
        (Privacy.PRIVATE, Privacy.PRIVATE),
        (Privacy.UNDETERMINED, Privacy.UNDETERMINED),
        (Privacy.UNDETERMINED, None),
        (Privacy.PUBLIC, DummyHasPrivacy(privacy=Privacy.PUBLIC)),
        (Privacy.PRIVATE, DummyHasPrivacy(privacy=Privacy.PRIVATE)),
        (Privacy.UNDETERMINED, DummyHasPrivacy(privacy=Privacy.UNDETERMINED)),
    ],
)
async def test_resolve_privacy(
    expected: Privacy, privacy: Privacy | HasPrivacy | None
) -> None:
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
async def test_merge_privacies(expected: Privacy, privacies: tuple[Privacy]) -> None:
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
async def test_merge_secondary_privacies(
    expected: Privacy, privacies: tuple[Privacy]
) -> None:
    assert expected == merge_secondary_privacies(*privacies)
