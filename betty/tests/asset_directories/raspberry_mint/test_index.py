import pytest

from betty.content_builder import ContentBuilderManufacturer
from betty.content_builders.render import Render, RenderData
from betty.dirs import asset_directory
from betty.project import Project
from betty.service_provider import ServiceProviderManufacturer
from betty.service_providers.raspberry_mint import (
    RaspberryMint,
    RaspberryMintData,
    Region,
)
from betty.test_utils.conftest import NewIsolatedProject


@pytest.fixture
def file() -> str:
    with open(
        asset_directory / "raspberry-mint" / "public" / "localized" / "index.html.j2",
        encoding="utf-8",
    ) as f:
        return f.read()


async def test_regional_content_front_page_summary(
    file: str, new_isolated_project: NewIsolatedProject
) -> None:
    async with new_isolated_project() as project:
        Project.service_providers.add_init_plugins(
            project,
            ServiceProviderManufacturer(
                RaspberryMint,
                RaspberryMintData(
                    regional_content={
                        Region.FRONT_PAGE_SUMMARY: [
                            ContentBuilderManufacturer(
                                Render,
                                RenderData("Hello, world!"),
                            ),
                        ]
                    }
                ),
            ),
        )
        async with project:
            environment = await project.jinja
            actual = await environment.from_string(file).render_async(
                document=await project.new_document()
            )
    assert "Hello, world!" in actual


async def test_regional_content_front_page_content(
    file: str, new_isolated_project: NewIsolatedProject
) -> None:
    async with new_isolated_project() as project:
        Project.service_providers.add_init_plugins(
            project,
            ServiceProviderManufacturer(
                RaspberryMint,
                RaspberryMintData(
                    regional_content={
                        Region.FRONT_PAGE_CONTENT: [
                            ContentBuilderManufacturer(
                                Render,
                                RenderData("Hello, world!"),
                            ),
                        ]
                    }
                ),
            ),
        )
        async with project:
            environment = await project.jinja
            actual = await environment.from_string(file).render_async(
                document=await project.new_document()
            )
    assert "Hello, world!" in actual
