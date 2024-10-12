from typing import Any, TYPE_CHECKING

import pytest

from betty.assertion.error import AssertionFailed
from betty.project.extension.wikipedia.config import WikipediaConfiguration
from betty.test_utils.assertion.error import raises_error

if TYPE_CHECKING:
    from collections.abc import Mapping
    from betty.serde.dump import Dump


class TestWikipediaConfiguration:
    async def test_load_with_minimal_configuration(self) -> None:
        dump: Mapping[str, Any] = {}
        WikipediaConfiguration().load(dump)

    async def test_load_without_dict_should_error(self) -> None:
        dump = None
        with raises_error(error_type=AssertionFailed):
            WikipediaConfiguration().load(dump)

    @pytest.mark.parametrize(
        "populate_images",
        [
            True,
            False,
        ],
    )
    async def test_load_with_populate_images(
        self, populate_images: bool | None
    ) -> None:
        dump: Dump = {
            "populate_images": populate_images,
        }
        sut = WikipediaConfiguration()
        sut.load(dump)
        assert sut.populate_images == populate_images

    async def test_dump_with_minimal_configuration(self) -> None:
        sut = WikipediaConfiguration()
        expected = {
            "populate_images": True,
        }
        assert sut.dump() == expected

    async def test_dump_with_populate_images(self) -> None:
        sut = WikipediaConfiguration()
        sut.populate_images = False
        expected = {
            "populate_images": False,
        }
        assert sut.dump() == expected
