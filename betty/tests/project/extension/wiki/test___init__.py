from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.link import Link
from betty.document import Document
from betty.job import Context as JobContext
from betty.project import Project
from betty.project.extension.wiki import Wiki
from betty.project.load import load
from betty.test_utils.project.extension import ExtensionTestBase
from betty.wiki.client import Summary

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.app import App
    from betty.project.extension import Extension


class TestWiki(ExtensionTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> Extension:
        async with Project.new_isolated(isolated_app) as project, project:
            return await Wiki.new_for_services(project)

    async def test_filters(self, sut: Wiki) -> None:
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
            project.configuration.extensions.enable(Wiki)
            async with project:
                jinja2_environment = await project.jinja2_environment
                actual = await jinja2_environment.from_string(
                    "{% for entry in (links | wikipedia_summary) %}{{ entry.content }}{% endfor %}"
                ).render_async(document=Document(job_context=JobContext()), links=links)

            m_get_summary.assert_called_once()
            assert actual == extract

    async def test_post_load(self, mocker: MockerFixture, isolated_app: App) -> None:
        m_populate_ancestry = mocker.patch(
            "betty.project.extension.wiki.jobs.PopulateEntity.do"
        )

        async with Project.new_isolated(isolated_app) as project:
            entity = Link("https://example.com")
            project.ancestry.add(entity)
            project.configuration.extensions.enable(Wiki)
            async with project:
                await load(project)

            m_populate_ancestry.assert_awaited_once()

    async def test_client(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(Wiki)
            async with project:
                extensions = await project.extensions
                wikipedia = extensions[Wiki]
                await wikipedia.client

    async def test_globals(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.enable(Wiki)
            async with project:
                extensions = await project.extensions
                sut = extensions[Wiki]
                assert sut.globals
