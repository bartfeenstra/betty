from __future__ import annotations

from typing import Sequence, Any, TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.privacy import (
    Privacy,
    HasPrivacy,
    is_public,
    merge_privacies,
    PrivacySchema,
    is_private,
    resolve_privacy,
)
from betty.test_utils.ancestry.privacy import DummyHasPrivacy
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.json.schema import SchemaTestBase

if TYPE_CHECKING:
    from betty.json.schema import Schema
    from betty.serde.dump import DumpMapping, Dump


class TestHasPrivacy:
    @pytest.mark.parametrize(
        ("privacy", "public", "private"),
        [
            (Privacy.PUBLIC, True, True),
            (Privacy.PUBLIC, False, True),
            (Privacy.PUBLIC, True, False),
            (Privacy.PUBLIC, False, False),
            (Privacy.PUBLIC, True, None),
            (Privacy.PUBLIC, False, None),
            (Privacy.PUBLIC, None, True),
            (Privacy.PUBLIC, None, False),
            (None, True, True),
            (None, True, False),
            (None, False, True),
            (None, False, False),
        ],
    )
    async def test___init___with_value_error(
        self, privacy: Privacy | None, public: bool | None, private: bool | None
    ) -> None:
        with pytest.raises(ValueError):  # noqa PT011
            DummyHasPrivacy(privacy=privacy, public=public, private=private)

    @pytest.mark.parametrize(
        ("expected", "privacy", "public", "private"),
        [
            (Privacy.UNDETERMINED, Privacy.UNDETERMINED, None, None),
            (Privacy.PUBLIC, Privacy.PUBLIC, None, None),
            (Privacy.PRIVATE, Privacy.PRIVATE, None, None),
            (Privacy.PUBLIC, None, True, None),
            (Privacy.UNDETERMINED, None, False, None),
            (Privacy.PRIVATE, None, None, True),
            (Privacy.UNDETERMINED, None, None, False),
        ],
    )
    async def test___init__(
        self,
        expected: Privacy,
        privacy: Privacy | None,
        public: bool | None,
        private: bool | None,
    ) -> None:
        sut = DummyHasPrivacy(privacy=privacy, public=public, private=private)
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
                DummyHasPrivacy(private=True),
            ),
            (
                {
                    "private": False,
                },
                DummyHasPrivacy(private=False),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: HasPrivacy
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected


class TestPrivacySchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [(PrivacySchema(), [True, False], [None, 123, "abc", [], {}])]


class TestIsPrivate:
    @pytest.mark.parametrize(
        ("expected", "target"),
        [
            (True, DummyHasPrivacy(privacy=Privacy.PRIVATE)),
            (False, DummyHasPrivacy(privacy=Privacy.PUBLIC)),
            (False, DummyHasPrivacy(privacy=Privacy.UNDETERMINED)),
            (False, object()),
        ],
    )
    async def test(self, expected: bool, target: Any) -> None:
        assert expected == is_private(target)


class TestIsPublic:
    @pytest.mark.parametrize(
        ("expected", "target"),
        [
            (False, DummyHasPrivacy(privacy=Privacy.PRIVATE)),
            (True, DummyHasPrivacy(privacy=Privacy.PUBLIC)),
            (True, DummyHasPrivacy(privacy=Privacy.UNDETERMINED)),
            (True, object()),
        ],
    )
    async def test(self, expected: bool, target: Any) -> None:
        assert expected == is_public(target)


class TestResolvePrivacy:
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
    async def test(
        self, expected: Privacy, privacy: Privacy | HasPrivacy | None
    ) -> None:
        assert resolve_privacy(privacy) == expected


class TestMergePrivacies:
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
    async def test(self, expected: Privacy, privacies: tuple[Privacy]) -> None:
        assert expected == merge_privacies(*privacies)
