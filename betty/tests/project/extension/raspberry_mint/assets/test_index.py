import pytest

from betty.app import App
from betty.content_provider.content_providers import Render, RenderConfiguration
from betty.dirs import ROOT_DIRECTORY_PATH
from betty.plugin.config import (
    PluginInstanceConfiguration,
    PluginInstanceConfigurationSequence,
)
from betty.project import Project
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.raspberry_mint.config import RaspberryMintConfiguration
from betty.project.extension.theme.config import RegionalContentConfiguration


@pytest.fixture
def file() -> str:
    with open(
        ROOT_DIRECTORY_PATH
        / "betty"
        / "project"
        / "extension"
        / "raspberry_mint"
        / "assets"
        / "public"
        / "localized"
        / "index.html.j2"
    ) as f:
        return f.read()


async def test_regional_content_front_page_summary(
    file: str, isolated_app: App
) -> None:
    async with Project.new_isolated(isolated_app) as project:
        project.configuration.extensions.append(
            PluginInstanceConfiguration(
                RaspberryMint,
                RaspberryMintConfiguration(
                    regional_content=RegionalContentConfiguration(
                        {
                            "front-page-summary": PluginInstanceConfigurationSequence(
                                [
                                    PluginInstanceConfiguration(
                                        Render,
                                        RenderConfiguration("Hello, world!"),
                                    ),
                                ]
                            )
                        }
                    )
                ),
            )
        )

        async with project:
            environment = await project.jinja2_environment
            actual = await environment.from_string(file).render_async(
                document=await project.new_document()
            )
    assert "Hello, world!" in actual


async def test_regional_content_front_page_content(
    file: str, isolated_app: App
) -> None:
    async with Project.new_isolated(isolated_app) as project:
        project.configuration.extensions.append(
            PluginInstanceConfiguration(
                RaspberryMint,
                RaspberryMintConfiguration(
                    regional_content=RegionalContentConfiguration(
                        {
                            "front-page-content": PluginInstanceConfigurationSequence(
                                [
                                    PluginInstanceConfiguration(
                                        Render,
                                        RenderConfiguration("Hello, world!"),
                                    ),
                                ]
                            )
                        }
                    )
                ),
            )
        )

        async with project:
            environment = await project.jinja2_environment
            actual = await environment.from_string(file).render_async(
                document=await project.new_document()
            )
    assert "Hello, world!" in actual
