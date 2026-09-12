import pytest

from betty.content_builder import NewContentBuilder
from betty.content_builders.render import Render, RenderConfig
from betty.dirs import asset_directory
from betty.service_provider import NewServiceProvider
from betty.service_providers.raspberry_mint import (
    RaspberryMint,
    RaspberryMintConfig,
    Region,
)
from betty.test_utils.conftest import IsolatedProjectFactory


@pytest.fixture
def file() -> str:
    with open(
        asset_directory / "raspberry-mint" / "public" / "localized" / "index.html.j2",
        encoding="utf-8",
    ) as f:
        return f.read()


async def test_regional_content_front_page_summary(
    file: str, isolated_project_factory: IsolatedProjectFactory
) -> None:
    async with isolated_project_factory(
        service_providers=[
            NewServiceProvider(
                RaspberryMint,
                RaspberryMintConfig(
                    regional_content={
                        Region.FRONT_PAGE_SUMMARY: [
                            NewContentBuilder(
                                Render,
                                RenderConfig("Hello, world!"),
                            ),
                        ]
                    }
                ),
            )
        ],
    ) as project:
        environment = await project.jinja
        actual = await environment.from_string(file).render_async(
            document=await project.new_document()
        )
    assert "Hello, world!" in actual


async def test_regional_content_front_page_content(
    file: str, isolated_project_factory: IsolatedProjectFactory
) -> None:
    async with isolated_project_factory(
        service_providers=[
            NewServiceProvider(
                RaspberryMint,
                RaspberryMintConfig(
                    regional_content={
                        Region.FRONT_PAGE_CONTENT: [
                            NewContentBuilder(
                                Render,
                                RenderConfig("Hello, world!"),
                            ),
                        ]
                    }
                ),
            )
        ],
    ) as project:
        environment = await project.jinja
        actual = await environment.from_string(file).render_async(
            document=await project.new_document()
        )
    assert "Hello, world!" in actual
