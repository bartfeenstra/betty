from collections.abc import AsyncIterator

import pytest
from playwright.async_api import expect, Page

from betty import serve
from betty.app import App
from betty.project import Project
from betty.project.extension.http_api_doc import HttpApiDoc
from betty.project.generate import generate
from betty.serve import Server


class TestSwaggerUi:
    @pytest.fixture(scope="session")
    async def served_project(self) -> AsyncIterator[tuple[Project, Server]]:
        async with (
            App.new_temporary() as app,
            app,
            Project.new_temporary(app) as project,
        ):
            project.configuration.extensions.enable(HttpApiDoc)
            async with project:
                await generate(project)
                async with await serve.BuiltinProjectServer.new_for_project(
                    project
                ) as server:
                    yield project, server

    @pytest.mark.asyncio(loop_scope="session")
    async def test(self, page: Page, served_project: tuple[Project, Server]) -> None:
        project, server = served_project
        await page.goto(server.public_url + "/api/index.html")
        locator = page.locator("#swagger-ui")
        # Test a couple of keywords in the source.
        await expect(locator).to_contain_text("Betty")
        await expect(locator).to_contain_text("api/index.json")
        # Test a couple of keywords shown after successful rendering.
        await expect(locator).to_contain_text("Retrieve a single")
        await expect(locator).to_contain_text("Retrieve the collection")
        await page.close()
