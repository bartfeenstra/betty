from collections.abc import AsyncIterator

import pytest
from playwright.async_api import expect, Page

from betty import serve
from betty.ancestry.person import Person
from betty.ancestry.person_name import PersonName
from betty.app import App
from betty.project import Project
from betty.project.extension.cotton_candy import CottonCandy
from betty.project.generate import generate
from betty.serve import Server


class TestSearchUi:
    @pytest.fixture(scope="session")
    async def served_project(self) -> AsyncIterator[tuple[Project, Server]]:
        person_id = "I0001"
        person = Person(id=person_id)
        person_individual_name = "Janet"
        PersonName(individual=person_individual_name, person=person)
        async with (
            App.new_temporary() as app,
            app,
            Project.new_temporary(app) as project,
        ):
            project.configuration.extensions.enable(CottonCandy)
            project.ancestry[Person].add(person)
            async with project:
                await generate(project)
                async with await serve.BuiltinProjectServer.new_for_project(
                    project
                ) as server:
                    yield project, server

    @pytest.mark.asyncio(loop_scope="session")
    async def test(self, page: Page, served_project: tuple[Project, Server]) -> None:
        project, server = served_project
        person = project.ancestry[Person]["I0001"]
        await page.goto(server.public_url)
        search_query = page.locator("#search-query")
        individual_name = person.names[0].individual
        assert individual_name
        await search_query.fill(individual_name)
        await search_query.press("ArrowDown")
        await expect(page.locator("#search-results")).to_be_visible()
        await page.keyboard.press("ArrowDown")
        await page.locator(":focus").press("Enter")
        assert page.url == f"{server.public_url}/person/{person.id}/index.html"
        await page.close()
