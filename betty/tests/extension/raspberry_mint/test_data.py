from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.content_provider import ContentProviderManufacturer
from betty.exception import HumanFacingException
from betty.extension.raspberry_mint import RaspberryMint
from betty.extension.raspberry_mint.data import (
    RaspberryMintConfiguration,
    ResolvableRegionalContent,
)
from betty.project import Project
from betty.test_utils.data import DataTestBase

if TYPE_CHECKING:
    from betty.app import App
    from betty.data.indicator import Path


class TestRaspberryMintConfiguration(DataTestBase[RaspberryMintConfiguration]):
    sut_cls = RaspberryMintConfiguration

    async def test_validate__should_validate_featured_entities_configuration(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        sut = RaspberryMintConfiguration(regional_content={"unknown-region": []})
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
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
        content_provider = ContentProviderManufacturer("my-first-plugin")
        regional_content: ResolvableRegionalContent = {
            "front": content_provider,
        }  # ty:ignore[invalid-assignment]
        sut = RaspberryMintConfiguration(regional_content=regional_content)
        assert sut.regional_content["front"][0] is content_provider
