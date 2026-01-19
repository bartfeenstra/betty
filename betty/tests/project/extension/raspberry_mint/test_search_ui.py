from collections.abc import AsyncIterator  # noqa: I001
from pathlib import Path

import pytest
from aiofiles.tempfile import TemporaryDirectory
from playwright.async_api import Page, expect

from betty import serve
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.app import App
from betty.project import Project
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.generate import generate
from betty.serve import Server
from betty.tests.conftest import check_skip_playwright


class TestSearchUi:
    INDIVIDUAL_NAME = "Janet"

    @pytest.fixture(scope="session")
    async def served_project(self) -> AsyncIterator[tuple[Project, Server]]:
        person_id = "I0001"
        person = Person(id=person_id)
        PersonName(individual=self.INDIVIDUAL_NAME, person=person)
        async with (
            TemporaryDirectory() as cache_directory_path_str,
            App.new_isolated(
                cache_directory_path=Path(cache_directory_path_str)
            ) as app,
            app,
            Project.new_isolated(app) as project,
        ):
            project.configuration.extensions.enable(RaspberryMint)
            project.ancestry[Person].add(person)
            async with project:
                await generate(project)
                async with await serve.BuiltinProjectServer.new_for_services(
                    project
                ) as server:
                    yield project, server

    @pytest.mark.asyncio(loop_scope="session")
    @check_skip_playwright
    async def test(self, page: Page, served_project: tuple[Project, Server]) -> None:
        project, server = served_project
        await page.goto(server.public_url)

        # Enter the search.
        entry_point = page.locator(".header-entry-point-search").locator("visible=true")
        await entry_point.click(force=True)
        await expect(page.locator("#search-form")).to_be_visible()

        # Search for a person's name.
        await page.keyboard.type(self.INDIVIDUAL_NAME)
        await page.locator(":focus").press("Enter")

        # Assert there is a search result.
        search_results_container = page.locator("#search-results-container")
        await expect(search_results_container).to_be_visible()
        search_result = search_results_container.locator(".search-result")
        await expect(search_result).to_have_count(1)

        # Follow the search result's link.
        search_result_link = search_result.locator("a")
        await search_result_link.evaluate(
            "searchResultLink => searchResultLink.click()"
        )

        # Assert we're at the page linked to by the search result.
        person = project.ancestry[Person]["I0001"]
        await expect(page).to_have_url(
            f"{server.public_url}/person/{person.public_id}/index.html"
        )
        await page.close()
