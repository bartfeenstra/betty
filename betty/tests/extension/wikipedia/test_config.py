from pathlib import Path
from typing import Any

import pytest

from betty.extension.wikipedia.config import WikipediaConfiguration
from betty.serde.dump import Dump
from betty.serde.load import AssertionFailed
from betty.tests.serde import raises_error


class TestWikipediaConfiguration:
    async def test_load_with_minimal_configuration(self) -> None:
        dump: dict[str, Any] = {}
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
        sut = WikipediaConfiguration.load(dump)
        assert sut.populate_images == populate_images

    async def test_dump_with_minimal_configuration(self) -> None:
        sut = WikipediaConfiguration()
        expected = {
            "populate_images": True,
        }
        assert expected == sut.dump()

    async def test_dump_with_populate_images(self) -> None:
        sut = WikipediaConfiguration()
        sut.populate_images = False
        expected = {
            "populate_images": False,
        }
        assert expected == sut.dump()

    async def test_update(self, tmp_path: Path) -> None:
        sut = WikipediaConfiguration()
        other = WikipediaConfiguration()
        other.populate_images = False
        sut.update(other)
        assert sut.populate_images is False
