import pytest

from betty import ROOT_DIRECTORY_PATH
from betty.app import App
from betty.plugin.config import PluginInstanceConfiguration
from betty.project import Project
from betty.project.extension.raspberry_mint import RaspberryMint


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
    file: str, temporary_app: App
) -> None:
    async with Project.new_temporary(temporary_app) as project:
        project.configuration.extensions.append(
            PluginInstanceConfiguration(
                RaspberryMint,
                configuration={
                    "regional_content": {
                        "front-page-summary": [
                            {"id": "plain-text", "configuration": "Hello, world!"},
                        ]
                    }
                },
            )
        )

        async with project:
            environment = await project.jinja2_environment
            actual = await environment.from_string(file).render_async(
                resource=await project.new_resource_context()
            )
    assert "Hello, world!" in actual


async def test_regional_content_front_page_content(
    file: str, temporary_app: App
) -> None:
    async with Project.new_temporary(temporary_app) as project:
        project.configuration.extensions.append(
            PluginInstanceConfiguration(
                RaspberryMint,
                configuration={
                    "regional_content": {
                        "front-page-content": [
                            {"id": "plain-text", "configuration": "Hello, world!"},
                        ]
                    }
                },
            )
        )

        async with project:
            environment = await project.jinja2_environment
            actual = await environment.from_string(file).render_async(
                resource=await project.new_resource_context()
            )
    assert "Hello, world!" in actual
