from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.ancestry import Ancestry
from betty.ancestry.has_file_references import HasFileReferences
from betty.model import Entity
from betty.model.association import BidirectionalToZeroOrOne
from betty.test_utils.ancestry.date import DummyHasDate
from betty.test_utils.model import DummyEntity
from betty.test_utils.model.collections import EntityCollectionTestBase

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.model.collections import EntityCollection


class DummyHasDateWithContextDefinitions(DummyHasDate):
    @override
    def dated_linked_data_contexts(self) -> tuple[str | None, str | None, str | None]:
        return "single-date", "start-date", "end-date"


class DummyHasFileReferences(HasFileReferences, DummyEntity):
    pass


class _TestAncestry_OneToOne_Left(DummyEntity):
    one_right = BidirectionalToZeroOrOne[
        "_TestAncestry_OneToOne_Left", "_TestAncestry_OneToOne_Right"
    ](
        "betty.tests.ancestry.test___init__:_TestAncestry_OneToOne_Left",
        "one_right",
        "betty.tests.ancestry.test___init__:_TestAncestry_OneToOne_Right",
        "one_left",
    )


class _TestAncestry_OneToOne_Right(DummyEntity):
    one_left = BidirectionalToZeroOrOne[
        "_TestAncestry_OneToOne_Right", _TestAncestry_OneToOne_Left
    ](
        "betty.tests.ancestry.test___init__:_TestAncestry_OneToOne_Right",
        "one_left",
        "betty.tests.ancestry.test___init__:_TestAncestry_OneToOne_Left",
        "one_right",
    )


class TestAncestry(EntityCollectionTestBase[Entity]):
    @override
    async def get_suts(self) -> Sequence[EntityCollection[Entity]]:
        return (Ancestry(),)

    @override
    async def get_entities(
        self,
    ) -> Sequence[Entity]:
        return (
            _TestAncestry_OneToOne_Left(),
            _TestAncestry_OneToOne_Right(),
            DummyEntity(),
        )

    async def test_add_(self) -> None:
        sut = Ancestry()
        left = _TestAncestry_OneToOne_Left()
        right = _TestAncestry_OneToOne_Right()
        left.one_right = right
        sut.add(left)
        assert left in sut
        assert right in sut

    async def test_unchecked(self) -> None:
        sut = Ancestry()
        left = _TestAncestry_OneToOne_Left()
        right = _TestAncestry_OneToOne_Right()
        left.one_right = right
        with sut.unchecked():
            sut.add(left)
        assert left in sut
        assert right not in sut
