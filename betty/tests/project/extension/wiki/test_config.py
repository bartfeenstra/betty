from typing import TYPE_CHECKING, Any

import pytest

from betty.exception import HumanFacingException
from betty.project.extension.wiki.config import WikiConfiguration
from betty.test_utils.config import ConfigurationTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.serde import SerializedData


class TestWikiConfiguration(ConfigurationTestBase[WikiConfiguration]):
    sut_cls = WikiConfiguration

    async def test_load__with_minimal_configuration(self) -> None:
        serialized: Mapping[str, Any] = {}
        WikiConfiguration.load(serialized)

    async def test_load__without_dict_should_error(self) -> None:
        serialized = None
        with pytest.raises(HumanFacingException):
            WikiConfiguration.load(serialized)

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
        serialized: SerializedData = {
            "populate_images": populate_images,
        }
        sut = WikiConfiguration.load(serialized)
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
