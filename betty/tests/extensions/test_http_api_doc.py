from collections.abc import AsyncIterator

import pytest
from playwright.async_api import Page, expect

from betty.extensions.http_api_doc import HttpApiDoc
from betty.project import Project
from betty.project.generate import generate
from betty.server import Server
from betty.servers import project_builtin
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.tests.conftest import (
    check_skip_playwright,
    check_skip_webpack_entry_point_provider,
)


class TestHttpApiDoc:
    @pytest.mark.order(0)
    @check_skip_webpack_entry_point_provider
    async def test_generate(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(extensions=[HttpApiDoc]) as project:
            await generate(project)
            assert (project.www_directory / "api" / "index.html").is_file()
            assert (
                project.www_directory / "js" / "webpack" / "http-api-doc.js"
            ).is_file()


class TestSwaggerUi:
    @pytest.fixture(scope="session")
    async def served_project(self) -> AsyncIterator[tuple[Project, Server]]:
        async with Project.new_isolated(extensions=[HttpApiDoc]) as project:
            await generate(project)
            async with await project_builtin.ProjectBuiltinServer.new(
                project
            ) as server:
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
