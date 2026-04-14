from collections.abc import AsyncIterator

import pytest
from playwright.async_api import Page, expect

from betty import serve
from betty.plugins.extension.http_api_doc import HttpApiDoc
from betty.project import Project
from betty.project.generate import generate
from betty.serve import Server
from betty.tests.conftest import (
    check_skip_playwright,
    check_skip_webpack_entry_point_provider,
)


class TestSwaggerUi:
    @pytest.fixture(scope="session")
    async def served_project(self) -> AsyncIterator[tuple[Project, Server]]:
        async with Project.new_isolated(service_plugins=[HttpApiDoc]) as project:
            await generate(project)
            async with await serve.BuiltinProjectServer.new(project) as server:
                yield project, server

    @pytest.mark.asyncio(loop_scope="session")
    @pytest.mark.order(0)
    @check_skip_playwright
    @check_skip_webpack_entry_point_provider
    async def test(self, page: Page, served_project: tuple[Project, Server]) -> None:
        _project, server = served_project
        await page.goto(server.public_url + "/api/index.html")
        locator = page.locator("#swagger-ui")
        # Test a couple of keywords in the source.
        await expect(locator).to_contain_text("Betty")
        await expect(locator).to_contain_text("api/index.json")
        # Test a couple of keywords shown after successful rendering.
        await expect(locator).to_contain_text("Retrieve a single")
        await expect(locator).to_contain_text("Retrieve the collection")
        await page.close()
