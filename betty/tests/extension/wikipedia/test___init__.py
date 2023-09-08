from __future__ import annotations

from typing import Any

from aioresponses import aioresponses

from betty.app import App
from betty.extension import Wikipedia
from betty.load import load
from betty.media_type import MediaType
from betty.model.ancestry import Source, Link
from betty.project import ExtensionConfiguration
from betty.task import Context
from betty.tests import patch_cache


class TestWikipedia:
    @patch_cache
    async def test_filter(self, aioresponses: aioresponses) -> None:
        entry_url = 'https://en.wikipedia.org/wiki/Amsterdam'
        links = [
            Link(entry_url),
            # Add a link to Wikipedia, but using a locale that's not used by the app, to test it's ignored.
            Link('https://nl.wikipedia.org/wiki/Amsterdam'),
            # Add a link that doesn't point to Wikipedia at all to test it's ignored.
            Link('https://example.com'),
        ]
        api_url = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=extracts&exintro&format=json&formatversion=2'
        title = 'Amstelredam'
        extract = 'De hoofdstad van Nederland.'
        api_response_body = {
            'query': {
                'pages': [
                    {
                        'title': title,
                        'extract': extract,
                    },
                ],
            }
        }
        aioresponses.get(api_url, payload=api_response_body)

        async with App() as app:
            app.project.configuration.extensions.append(ExtensionConfiguration(Wikipedia))
            actual = await app.jinja2_environment.from_string(
                '{% for entry in (links | wikipedia) %}{{ entry.content }}{% endfor %}').render_async(
                task_context=Context(),
                links=links,
            )
        assert extract == actual

    @patch_cache
    async def test_post_load(self, aioresponses: aioresponses) -> None:
        resource = Source(
            id='the_source',
            name='The Source',
        )
        link = Link('https://en.wikipedia.org/wiki/Amsterdam')
        resource.links.add(link)
        entry_title = 'Amstelredam'
        entry_extract = 'Capitol of the Netherlands'
        entry_api_response_body = {
            'query': {
                'pages': [
                    {
                        'title': entry_title,
                        'extract': entry_extract,
                    },
                ],
            }
        }
        entry_api_url = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=extracts&exintro&format=json&formatversion=2'
        aioresponses.get(entry_api_url, payload=entry_api_response_body)
        translations_api_response_body: Any = {
            'query': {
                'pages': [
                    {
                        'langlinks': [],
                    },
                ],
            },
        }
        translations_api_url = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=langlinks&lllimit=500&format=json&formatversion=2'
        aioresponses.get(translations_api_url, payload=translations_api_response_body)

        async with App() as app:
            app.project.configuration.extensions.append(ExtensionConfiguration(Wikipedia))
            app.project.ancestry.add(resource)
            await load(app)

        assert 1 == len(resource.links)
        assert entry_title == link.label
        assert 'en' == link.locale
        assert MediaType('text/html') == link.media_type
        assert link.description is not None
        assert 'external' == link.relationship
