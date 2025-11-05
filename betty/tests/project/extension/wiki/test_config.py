from typing import TYPE_CHECKING, Any

import pytest

from betty.exception import HumanFacingException
from betty.project.extension.wiki.config import WikiConfiguration

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.serde.dump import Dump


class TestWikiConfiguration:
    async def test_load__with_minimal_configuration(self) -> None:
        dump: Mapping[str, Any] = {}
        WikiConfiguration().load(dump)

    async def test_load__without_dict_should_error(self) -> None:
        dump = None
        with pytest.RaisesGroup(HumanFacingException):
            WikiConfiguration().load(dump)

    @pytest.mark.parametrize(
        "populate_images",
        [
            True,
            False,
        ],
    )
    async def test_load__with_populate_images(
        self, populate_images: bool | None
    ) -> None:
        dump: Dump = {
            "populate_images": populate_images,
        }
        sut = WikiConfiguration()
        sut.load(dump)
        assert sut.populate_images == populate_images

    async def test_dump__with_minimal_configuration(self) -> None:
        sut = WikiConfiguration()
        expected = {
            "populate_images": True,
        }
        assert sut.dump() == expected

    async def test_dump__with_populate_images(self) -> None:
        sut = WikiConfiguration()
        sut.populate_images = False
        expected = {
            "populate_images": False,
        }
        assert sut.dump() == expected
