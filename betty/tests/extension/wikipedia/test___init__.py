from __future__ import annotations


from betty.extension import Wikipedia
from betty.job import Context
from betty.load import load
from betty.model.ancestry import Link
from betty.project import ExtensionConfiguration, Project
from betty.wikipedia import Summary
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.app import App
    from pytest_mock import MockerFixture


class TestWikipedia:
    async def test_filter(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        language = "en"
        name = "Amsterdam"
        title = "Amstelredam"
        extract = "De hoofdstad van Nederland."
        summary = Summary(language, name, title, extract)

        m_get_summary = mocker.patch("betty.wikipedia._Retriever.get_summary")
        m_get_summary.return_value = summary

        page_url = f"https://{language}.wikipedia.org/wiki/{name}"
        links = [
            Link(page_url),
            # Add a link to Wikipedia, but using a locale that's not used by the app, to test it's ignored.
            Link("https://nl.wikipedia.org/wiki/Amsterdam"),
            # Add a link that doesn't point to Wikipedia at all to test it's ignored.
            Link("https://example.com"),
        ]

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.append(ExtensionConfiguration(Wikipedia))
            async with project:
                actual = await project.jinja2_environment.from_string(
                    "{% for entry in (links | wikipedia) %}{{ entry.content }}{% endfor %}"
                ).render_async(
                    job_context=Context(),
                    links=links,
                )

            m_get_summary.assert_called_once()
            assert extract == actual

    async def test_post_load(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        m_populate = mocker.patch("betty.wikipedia._Populator.populate")

        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.append(ExtensionConfiguration(Wikipedia))
            async with project:
                await load(project)

            m_populate.assert_called_once()
