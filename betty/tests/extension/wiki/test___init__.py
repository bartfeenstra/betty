from __future__ import annotations

from typing import TYPE_CHECKING

from betty.ancestry.link import Link
from betty.document import Document
from betty.extension.wiki import Wiki
from betty.job import Context
from betty.project import Project
from betty.project.load import load
from betty.wiki.client import Summary

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.app import App


class TestWiki:
    async def test_filters(self, isolated_app: App) -> None:
        async with (
            Project.new_isolated(isolated_app) as project,
            project,
            await Wiki.new(project) as sut,
        ):
            assert sut.filters

    async def test_filter_wikipedia_summary_links(
        self, mocker: MockerFixture, isolated_app: App
    ) -> None:
        language = "en"
        name = "Amsterdam"
        title = "Amstelredam"
        extract = "De hoofdstad van Nederland."
        summary = Summary(language, name, title, extract)

        m_get_summary = mocker.patch("betty.wiki.client.Client.get_summary")
        m_get_summary.return_value = summary

        page_url = f"https://{language}.wikipedia.org/wiki/{name}"
        links = [
            Link(page_url),
            # Add a link to Wikipedia, but using a locale that's not used by the app, to test it's ignored.
            Link("https://nl.wikipedia.org/wiki/Amsterdam"),
            # Add a link that doesn't point to Wikipedia at all to test it's ignored.
            Link("https://example.com"),
        ]

        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Wiki)
            async with project:
                jinja = await project.jinja
                actual = await jinja.from_string(
                    "{% for entry in (links | wikipedia_summary) %}{{ entry.content }}{% endfor %}"
                ).render_async(document=Document(context=Context()), links=links)

            m_get_summary.assert_called_once()
            assert actual == extract

    async def test_post_load(self, mocker: MockerFixture, isolated_app: App) -> None:
        m_populate_ancestry = mocker.patch(
            "betty.extension.wiki.jobs.PopulateEntity.do"
        )

        async with Project.new_isolated(isolated_app) as project:
            entity = Link("https://example.com")
            project.ancestry.add(entity)
            project.configuration.extensions.add(Wiki)
            async with project:
                await load(project)

            m_populate_ancestry.assert_awaited_once()

    async def test_client(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Wiki)
            async with project:
                extensions = await project.extensions
                wikipedia = extensions[Wiki]
                await wikipedia.client

    async def test_globals(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(Wiki)
            async with project:
                extensions = await project.extensions
                sut = extensions[Wiki]
                assert sut.globals
