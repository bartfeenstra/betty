import pytest

from betty.app import App
from betty.content import ContentManufacturer
from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.extension import ExtensionManufacturer
from betty.plugins.content.render import Render, RenderConfiguration
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.plugins.extension.raspberry_mint.data import RaspberryMintConfiguration
from betty.project import Project


@pytest.fixture
def file() -> str:
    with open(
        ASSETS_DIRECTORY_PATH
        / "raspberry-mint"
        / "public"
        / "localized"
        / "index.html.j2"
    ) as f:
        return f.read()


async def test_regional_content_front_page_summary(
    file: str, isolated_app: App
) -> None:
    async with Project.new_isolated(isolated_app) as project:
        project.configuration.extensions.add(
            ExtensionManufacturer(
                RaspberryMint,
                RaspberryMintConfiguration(
                    regional_content={
                        "front-page-summary": [
                            ContentManufacturer(
                                Render,
                                RenderConfiguration("Hello, world!"),
                            ),
                        ]
                    }
                ),
            )
        )

        async with project:
            environment = await project.jinja
            actual = await environment.from_string(file).render_async(
                document=await project.new_document()
            )
    assert "Hello, world!" in actual


async def test_regional_content_front_page_content(
    file: str, isolated_app: App
) -> None:
    async with Project.new_isolated(isolated_app) as project:
        project.configuration.extensions.add(
            ExtensionManufacturer(
                RaspberryMint,
                RaspberryMintConfiguration(
                    regional_content={
                        "front-page-content": [
                            ContentManufacturer(
                                Render,
                                RenderConfiguration("Hello, world!"),
                            ),
                        ]
                    }
                ),
            )
        )

        async with project:
            environment = await project.jinja
            actual = await environment.from_string(file).render_async(
                document=await project.new_document()
            )
    assert "Hello, world!" in actual
