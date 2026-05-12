from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.privacy import Privacy
from betty.test_utils.privacy import DummyHasPrivacy

if TYPE_CHECKING:
    from betty.attrs.privacy import HasPrivacy
    from betty.portable import PortableMapping
    from betty.test_utils.conftest import AssertLinkedDataDump


class TestPrivacyAttr:
    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                True,
                DummyHasPrivacy(privacy=Privacy.PRIVATE),
            ),
            (
                False,
                DummyHasPrivacy(privacy=Privacy.PUBLIC),
            ),
        ],
    )
    async def test_dump_linked_data_for(
        self,
        assert_linked_data_dump: AssertLinkedDataDump,
        expected: PortableMapping,
        sut: HasPrivacy,
    ) -> None:
        assert (
            await assert_linked_data_dump(
                type(sut)._privacy.linked_data_schema_for,
                lambda project: type(sut)._privacy.dump_linked_data_for(project, sut),
            )
            == expected
        )


class TestHasPrivacy:
    @pytest.mark.parametrize(
        ("expected", "privacy"),
        [
            (Privacy.UNDETERMINED, Privacy.UNDETERMINED),
            (Privacy.PUBLIC, Privacy.PUBLIC),
            (Privacy.PRIVATE, Privacy.PRIVATE),
        ],
    )
    def test___init__(self, expected: Privacy, privacy: Privacy) -> None:
        sut = DummyHasPrivacy(privacy=privacy)
        assert sut.privacy is expected

    def test_privacy(self) -> None:
        sut = DummyHasPrivacy()
        privacy = Privacy.PUBLIC
        sut.privacy = privacy
        assert sut.privacy is privacy
        del sut.privacy
        assert sut.privacy is Privacy.UNDETERMINED

    def test_own_privacy(self) -> None:
        sut = DummyHasPrivacy()
        privacy = Privacy.PUBLIC
        sut.privacy = privacy
        assert sut.own_privacy is privacy

    def test_public(self) -> None:
        sut = DummyHasPrivacy()
        sut.public = True
        assert sut.public
        assert sut.privacy is Privacy.PUBLIC

    def test_private(self) -> None:
        sut = DummyHasPrivacy()
        sut.private = True
        assert sut.private
        assert sut.privacy is Privacy.PRIVATE
