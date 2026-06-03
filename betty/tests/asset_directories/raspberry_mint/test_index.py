import pytest

from betty.content import ContentManufacturer
from betty.dirs import ASSET_DIRECTORY
from betty.extension import ExtensionManufacturer
from betty.extensions.raspberry_mint import (
    RaspberryMint,
    RaspberryMintData,
    Region,
)
from betty.plugins.content.render import Render, RenderData
from betty.test_utils.conftest import IsolatedProjectFactory


@pytest.fixture
def file() -> str:
    with open(
        ASSET_DIRECTORY / "raspberry-mint" / "public" / "localized" / "index.html.j2",
        encoding="utf-8",
    ) as f:
        return f.read()


async def test_regional_content_front_page_summary(
    file: str, isolated_project_factory: IsolatedProjectFactory
) -> None:
    async with isolated_project_factory(
        extensions=[
            ExtensionManufacturer(
                RaspberryMint,
                RaspberryMintData(
                    regional_content={
                        Region.FRONT_PAGE_SUMMARY: [
                            ContentManufacturer(
                                Render,
                                RenderData("Hello, world!"),
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
        extensions=[
            ExtensionManufacturer(
                RaspberryMint,
                RaspberryMintData(
                    regional_content={
                        Region.FRONT_PAGE_CONTENT: [
                            ContentManufacturer(
                                Render,
                                RenderData("Hello, world!"),
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
