from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.content import ContentManufacturer
from betty.exception import HumanFacingException
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.plugins.extension.raspberry_mint.data import (
    RaspberryMintConfiguration,
)
from betty.plugins.extension.raspberry_mint.region import Region
from betty.test_utils.data import DataTestBase

if TYPE_CHECKING:
    from betty.test_utils.conftest import IsolatedProjectFactory


class TestRaspberryMintConfiguration(DataTestBase[RaspberryMintConfiguration]):
    sut_cls = RaspberryMintConfiguration

    async def test_validate__should_validate_featured_entities_configuration(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        sut = RaspberryMintConfiguration(regional_content={"unknown-region": []})
        async with isolated_project_factory(service_plugins=[RaspberryMint]) as project:
            with pytest.raises(HumanFacingException) as exc_info:
                await sut.validate(project)
        assert 'data.regional_content["unknown-region"]' in str(exc_info.value)

    def test_primary_color__from___init__(self) -> None:
        color = "#000000"
        sut = RaspberryMintConfiguration(primary_color=color)
        assert sut.primary_color == color

    def test_secondary_color__from___init__(self) -> None:
        color = "#000000"
        sut = RaspberryMintConfiguration(secondary_color=color)
        assert sut.secondary_color == color

    def test_tertiary_color__from___init__(self) -> None:
        color = "#000000"
        sut = RaspberryMintConfiguration(tertiary_color=color)
        assert sut.tertiary_color == color

    def test_regional_content__from___init__(self) -> None:
        content = ContentManufacturer("my-first-plugin")
        sut = RaspberryMintConfiguration(
            regional_content={
                Region.FRONT_PAGE_CONTENT: content,
            }  # ty:ignore[invalid-argument-type]
        )
        assert sut.regional_content[Region.FRONT_PAGE_CONTENT][0] is content
