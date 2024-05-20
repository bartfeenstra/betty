from __future__ import annotations


from betty.app import App
from betty.extension import Wikipedia
from betty.job import Context
from betty.load import load
from betty.model.ancestry import Link
from betty.project import ExtensionConfiguration
from betty.wikipedia import Summary
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestWikipedia:
    async def test_filter(self, mocker: MockerFixture) -> None:
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

        async with App.new_temporary() as app, app:
            app.project.configuration.extensions.append(
                ExtensionConfiguration(Wikipedia)
            )
            actual = await app.jinja2_environment.from_string(
                "{% for entry in (links | wikipedia) %}{{ entry.content }}{% endfor %}"
            ).render_async(
                job_context=Context(),
                links=links,
            )

        m_get_summary.assert_called_once()
        assert extract == actual

    async def test_post_load(self, mocker: MockerFixture) -> None:
        m_populate = mocker.patch("betty.wikipedia._Populator.populate")

        async with App.new_temporary() as app, app:
            app.project.configuration.extensions.append(
                ExtensionConfiguration(Wikipedia)
            )
            await load(app)

        m_populate.assert_called_once()
