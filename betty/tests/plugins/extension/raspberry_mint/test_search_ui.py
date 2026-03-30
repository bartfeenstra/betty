from collections.abc import AsyncIterator

import pytest
from playwright.async_api import Page, expect

from betty import serve
from betty.plugins.entity.person import Person
from betty.plugins.entity.person_name import PersonName
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.project import Project
from betty.project.generate import generate
from betty.serve import Server
from betty.tests.conftest import (
    check_skip_playwright,
    check_skip_webpack_entry_point_provider,
)


class TestSearchUi:
    INDIVIDUAL_NAME = "Janet"

    @pytest.fixture(scope="session")
    async def served_project(self) -> AsyncIterator[tuple[Project, Server]]:
        person_id = "I0001"
        person = Person(id=person_id)
        PersonName(individual=self.INDIVIDUAL_NAME, person=person)
        async with Project.new_isolated(extensions=[RaspberryMint]) as project:
            project.ancestry[Person].add(person)
            await generate(project)
            async with await serve.BuiltinProjectServer.new(project) as server:
                yield project, server

    @pytest.mark.asyncio(loop_scope="session")
    @pytest.mark.order(0)
    @check_skip_playwright
    @check_skip_webpack_entry_point_provider
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
