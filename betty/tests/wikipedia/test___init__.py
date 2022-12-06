from time import sleep
from typing import Tuple, Optional, Any
from unittest.mock import call

import aiohttp
import pytest
from pytest_mock import MockerFixture

from betty.media_type import MediaType
from betty.project import LocaleConfiguration, ExtensionConfiguration
from betty.tempfile import TemporaryDirectory
from betty.tests import patch_cache

try:
    from unittest.mock import AsyncMock
except ImportError:
    from mock.mock import AsyncMock

from aioresponses import aioresponses

from betty.model.ancestry import Source, Link, Citation
from betty.load import load
from betty.wikipedia import Entry, _Retriever, NotAnEntryError, _parse_url, RetrievalError, _Populator, Wikipedia
from betty.app import App


class TestParseUrl:
    @pytest.mark.parametrize('expected, url', [
        (('en', 'Amsterdam'), 'http://en.wikipedia.org/wiki/Amsterdam',),
        (('nl', 'Amsterdam'), 'https://nl.wikipedia.org/wiki/Amsterdam',),
        (('en', 'Amsterdam'), 'http://en.wikipedia.org/wiki/Amsterdam',),
        (('en', 'Amsterdam'), 'https://en.wikipedia.org/wiki/Amsterdam/',),
        (('en', 'Amsterdam'), 'https://en.wikipedia.org/wiki/Amsterdam/some-path',),
        (('en', 'Amsterdam'), 'https://en.wikipedia.org/wiki/Amsterdam?some=query',),
        (('en', 'Amsterdam'), 'https://en.wikipedia.org/wiki/Amsterdam#some-fragment',),
    ])
    def test_should_return(self, expected: Tuple[str, str], url: str) -> None:
        assert expected == _parse_url(url)

    @pytest.mark.parametrize('url', [
        '',
        'ftp://en.wikipedia.org/wiki/Amsterdam',
        'https://en.wikipedia.org/w/index.php?title=Amsterdam&action=edit',
    ])
    def test_should_error(self, url: str) -> None:
        with pytest.raises(NotAnEntryError):
            _parse_url(url)


class TestEntry:
    def test_url(self) -> None:
        sut = Entry('nl', 'Amsterdam', 'Title for Amsterdam', 'Content for Amsterdam')
        assert 'https://nl.wikipedia.org/wiki/Amsterdam' == sut.url

    def test_title(self) -> None:
        title = 'Title for Amsterdam'
        sut = Entry('nl', 'Amsterdam', title, 'Content for Amsterdam')
        assert title == sut.title

    def test_content(self) -> None:
        content = 'Content for Amsterdam'
        sut = Entry('nl', 'Amsterdam', 'Title for Amsterdam', content)
        assert content == sut.content


class TestRetriever:
    @pytest.mark.parametrize('expected, response_pages_json', [
        ({}, {},),
        ({
            'nl': 'Amsterdam',
            'uk': 'Амстердам',
        }, {
            'langlinks': [
                {
                    'lang': 'nl',
                    'title': 'Amsterdam',
                },
                {
                    'lang': 'uk',
                    'title': 'Амстердам',
                },
            ],
        },),
    ])
    async def test_get_translations_should_return(self, expected, response_pages_json, aioresponses: aioresponses, mocker: MockerFixture) -> None:
        mocker.patch('sys.stderr')
        entry_language = 'en'
        entry_name = 'Amsterdam'
        api_url = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=langlinks&lllimit=500&format=json&formatversion=2' % (entry_language, entry_name)
        api_response_body = {
            'query': {
                'pages': [response_pages_json],
            },
        }
        aioresponses.get(api_url, payload=api_response_body)
        with TemporaryDirectory() as cache_directory_path:
            async with aiohttp.ClientSession() as session:
                translations = await _Retriever(session, cache_directory_path).get_translations(entry_language, entry_name)
        assert expected == translations

    async def test_get_translations_with_client_error_should_raise_retrieval_error(self, aioresponses: aioresponses, mocker: MockerFixture) -> None:
        mocker.patch('sys.stderr')
        entry_language = 'en'
        entry_name = 'Amsterdam'
        api_url = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=langlinks&lllimit=500&format=json&formatversion=2' % (entry_language, entry_name)
        aioresponses.get(api_url, exception=aiohttp.ClientError())
        with TemporaryDirectory() as cache_directory_path:
            with pytest.raises(RetrievalError):
                async with aiohttp.ClientSession() as session:
                    await _Retriever(session, cache_directory_path).get_translations(entry_language, entry_name)

    async def test_get_translations_with_invalid_json_response_should_raise_retrieval_error(self, aioresponses: aioresponses, mocker: MockerFixture) -> None:
        mocker.patch('sys.stderr')
        entry_language = 'en'
        entry_name = 'Amsterdam'
        api_url = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=langlinks&lllimit=500&format=json&formatversion=2' % (entry_language, entry_name)
        aioresponses.get(api_url, body='{Haha Im not rly JSON}')
        with TemporaryDirectory() as cache_directory_path:
            with pytest.raises(RetrievalError):
                async with aiohttp.ClientSession() as session:
                    await _Retriever(session, cache_directory_path).get_translations(entry_language, entry_name)

    @pytest.mark.parametrize('response_json', [
        {},
        {
            'query': {}
        },
        {
            'query': {
                'pages': {}
            }
        },
        {
            'query': {
                'pages': []
            }
        },
    ])
    async def test_get_translations_with_unexpected_json_response_should_raise_retrieval_error(self, response_json, mocker: MockerFixture, aioresponses: aioresponses) -> None:
        mocker.patch('sys.stderr')
        entry_language = 'en'
        entry_name = 'Amsterdam'
        api_url = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=langlinks&lllimit=500&format=json&formatversion=2' % (entry_language, entry_name)
        aioresponses.get(api_url, payload=response_json)
        with TemporaryDirectory() as cache_directory_path:
            with pytest.raises(RetrievalError):
                async with aiohttp.ClientSession() as session:
                    await _Retriever(session, cache_directory_path).get_translations(entry_language, entry_name)

    async def test_get_entry_should_return(self, aioresponses: aioresponses) -> None:
        entry_language = 'en'
        entry_name = 'Amsterdam'
        api_url = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=extracts&exintro&format=json&formatversion=2'
        entry_url = 'https://en.wikipedia.org/wiki/Amsterdam'
        title = 'Amstelredam'
        extract_1 = 'De hoofdstad van Nederland.'
        extract_4 = 'Niet de hoofdstad van Holland.'
        api_response_body_1 = {
            'query': {
                'pages': [
                    {
                        'title': title,
                        'extract': extract_1,
                    },
                ],
            }
        }
        api_response_body_4 = {
            'query': {
                'pages': [
                    {
                        'title': title,
                        'extract': extract_4,
                    },
                ],
            }
        }
        aioresponses.get(api_url, payload=api_response_body_1)
        aioresponses.get(api_url, exception=aiohttp.ClientError())
        aioresponses.get(api_url, payload=api_response_body_4)
        with TemporaryDirectory() as cache_directory_path:
            async with aiohttp.ClientSession() as session:
                retriever = _Retriever(session, cache_directory_path, 1)
                # The first retrieval should make a successful request and set the cache.
                entry_1 = await retriever.get_entry(entry_language, entry_name)
                # The second retrieval should hit the cache from the first request.
                entry_2 = await retriever.get_entry(entry_language, entry_name)
                # The third retrieval should result in a failed request, and hit the cache from the first request.
                sleep(2)
                entry_3 = await retriever.get_entry(entry_language, entry_name)
                # The fourth retrieval should make a successful request and set the cache again.
                entry_4 = await retriever.get_entry(entry_language, entry_name)
                # The fifth retrieval should hit the cache from the fourth request.
                entry_5 = await retriever.get_entry(entry_language, entry_name)
        for entry in [entry_1, entry_2, entry_3]:
            assert entry_url == entry.url
            assert title == entry.title
            assert extract_1 == entry.content
        for entry in [entry_4, entry_5]:
            assert entry_url == entry.url
            assert title == entry.title
            assert extract_4 == entry.content

    async def test_get_entry_with_client_error_should_raise_retrieval_error(self, aioresponses: aioresponses, mocker: MockerFixture) -> None:
        mocker.patch('sys.stderr')
        entry_language = 'en'
        entry_name = 'Amsterdam'
        api_url = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=extracts&exintro&format=json&formatversion=2'
        aioresponses.get(api_url, exception=aiohttp.ClientError())
        with TemporaryDirectory() as cache_directory_path:
            async with aiohttp.ClientSession() as session:
                retriever = _Retriever(session, cache_directory_path)
                with pytest.raises(RetrievalError):
                    await retriever.get_entry(entry_language, entry_name)


class TestPopulator:
    @patch_cache
    async def test_populate_link_should_convert_http_to_https(self, mocker: MockerFixture) -> None:
        m_retriever = mocker.patch('betty.wikipedia._Retriever')
        link = Link('http://en.wikipedia.org/wiki/Amsterdam')
        entry_language = 'nl'
        with App() as app:
            sut = _Populator(app, m_retriever)
            await sut.populate_link(link, entry_language)
        assert 'https://en.wikipedia.org/wiki/Amsterdam' == link.url

    @pytest.mark.parametrize('expected, media_type', [
        (MediaType('text/plain'), MediaType('text/plain')),
        (MediaType('text/html'), MediaType('text/html')),
        (MediaType('text/html'), None),
    ])
    @patch_cache
    async def test_populate_link_should_set_media_type(self, expected: MediaType, media_type: Optional[MediaType], mocker: MockerFixture) -> None:
        m_retriever = mocker.patch('betty.wikipedia._Retriever')
        link = Link('http://en.wikipedia.org/wiki/Amsterdam')
        link.media_type = media_type
        with App() as app:
            sut = _Populator(app, m_retriever)
            await sut.populate_link(link, 'en')
        assert expected == link.media_type

    @pytest.mark.parametrize('expected, relationship', [
        ('alternate', 'alternate'),
        ('external', 'external'),
        ('external', None),
    ])
    @patch_cache
    async def test_populate_link_should_set_relationship(self, expected: str, relationship: Optional[str], mocker: MockerFixture) -> None:
        m_retriever = mocker.patch('betty.wikipedia._Retriever')
        link = Link('http://en.wikipedia.org/wiki/Amsterdam')
        link.relationship = relationship
        with App() as app:
            sut = _Populator(app, m_retriever)
            await sut.populate_link(link, 'en')
        assert expected == link.relationship

    @pytest.mark.parametrize('expected, entry_language, locale', [
        ('nl-NL', 'nl', 'nl-NL'),
        ('nl', 'nl', None),
        ('nl', 'en', 'nl'),
    ])
    @patch_cache
    async def test_populate_link_should_set_locale(self, expected: str, entry_language: str, locale: Optional[str], mocker: MockerFixture) -> None:
        m_retriever = mocker.patch('betty.wikipedia._Retriever')
        link = Link('http://%s.wikipedia.org/wiki/Amsterdam' % entry_language)
        link.locale = locale
        with App() as app:
            sut = _Populator(app, m_retriever)
            await sut.populate_link(link, entry_language)
        assert expected == link.locale

    @pytest.mark.parametrize('expected, description', [
        ('This is the original description', 'This is the original description'),
        ('Read more on Wikipedia.', None),
    ])
    @patch_cache
    async def test_populate_link_should_set_description(self, expected: str, description: str, mocker: MockerFixture) -> None:
        m_retriever = mocker.patch('betty.wikipedia._Retriever')
        link = Link('http://en.wikipedia.org/wiki/Amsterdam')
        link.description = description
        entry_language = 'en'
        with App() as app:
            sut = _Populator(app, m_retriever)
            await sut.populate_link(link, entry_language)
        assert expected == link.description

    @pytest.mark.parametrize('expected, label', [
        ('Amsterdam', 'Amsterdam'),
        ('The city of Amsterdam', None),
    ])
    @patch_cache
    async def test_populate_link_should_set_label(self, expected: str, label: Optional[str], mocker: MockerFixture) -> None:
        m_retriever = mocker.patch('betty.wikipedia._Retriever')
        link = Link('http://en.wikipedia.org/wiki/Amsterdam')
        link.label = label
        entry = Entry('en', 'The_city_of_Amsterdam', 'The city of Amsterdam', 'Amsterdam, such a lovely place!')
        with App() as app:
            sut = _Populator(app, m_retriever)
            await sut.populate_link(link, 'en', entry)
        assert expected == link.label

    @patch_cache
    async def test_populate_should_ignore_resource_without_link_support(self, mocker: MockerFixture) -> None:
        m_retriever = mocker.patch('betty.wikipedia._Retriever')
        source = Source('The Source')
        resource = Citation('the_citation', source)
        with App() as app:
            app.project.ancestry.entities.append(resource)
            sut = _Populator(app, m_retriever)
            await sut.populate()

    @patch_cache
    async def test_populate_should_ignore_resource_without_links(self, mocker: MockerFixture) -> None:
        m_retriever = mocker.patch('betty.wikipedia._Retriever')
        resource = Source('the_source', 'The Source')
        with App() as app:
            app.project.ancestry.entities.append(resource)
            sut = _Populator(app, m_retriever)
            await sut.populate()
        assert set() == resource.links

    @patch_cache
    async def test_populate_should_ignore_non_wikipedia_links(self, mocker: MockerFixture) -> None:
        m_retriever = mocker.patch('betty.wikipedia._Retriever')
        link = Link('https://example.com')
        resource = Source('the_source', 'The Source')
        resource.links.add(link)
        with App() as app:
            app.project.ancestry.entities.append(resource)
            sut = _Populator(app, m_retriever)
            await sut.populate()
        assert {link} == resource.links

    @patch_cache
    async def test_populate_should_populate_existing_link(self, mocker: MockerFixture) -> None:
        m_retriever = mocker.patch('betty.wikipedia._Retriever', spec=_Retriever, new_callable=AsyncMock)
        entry_language = 'en'
        entry_name = 'Amsterdam'
        entry_title = 'Amsterdam'
        entry_content = 'Capitol of the Netherlands'
        entry = Entry(entry_language, entry_name, entry_title, entry_content)
        m_retriever.get_entry.return_value = entry

        resource = Source('the_source', 'The Source')
        link = Link('https://en.wikipedia.org/wiki/Amsterdam')
        resource.links.add(link)
        with App() as app:
            app.project.ancestry.entities.append(resource)
            sut = _Populator(app, m_retriever)
            await sut.populate()
        m_retriever.get_entry.assert_called_once_with(entry_language, entry_name)
        assert 1 == len(resource.links)
        assert 'Amsterdam' == link.label
        assert 'en' == link.locale
        assert MediaType('text/html') == link.media_type
        assert link.description is not None
        assert 'external' == link.relationship

    @patch_cache
    async def test_populate_should_add_translation_links(self, mocker: MockerFixture) -> None:
        m_retriever = mocker.patch('betty.wikipedia._Retriever', spec=_Retriever, new_callable=AsyncMock)
        entry_language = 'en'
        entry_name = 'Amsterdam'
        entry_title = 'Amsterdam'
        entry_content = 'Capitol of the Netherlands'
        entry = Entry(entry_language, entry_name, entry_title, entry_content)
        added_entry_language = 'nl'
        added_entry_name = 'Amsterdam'
        added_entry_title = 'Amsterdam'
        added_entry_content = 'Hoofdstad van Nederland'
        added_entry = Entry(added_entry_language, added_entry_name, added_entry_title, added_entry_content)
        m_retriever.get_entry.side_effect = [
            entry,
            added_entry
        ]

        m_retriever.get_translations.return_value = {
            entry_language: entry_name,
            added_entry_language: added_entry_name,
        }

        resource = Source('the_source', 'The Source')
        link_en = Link('https://en.wikipedia.org/wiki/Amsterdam')
        resource.links.add(link_en)
        app = App()
        app.project.configuration.locales['en-US'].alias = 'en'
        app.project.configuration.locales.append(LocaleConfiguration('nl-NL', 'nl'))
        with app:
            app.project.ancestry.entities.append(resource)
            sut = _Populator(app, m_retriever)
            await sut.populate()

        m_retriever.get_entry.assert_has_calls([
            call(entry_language, entry_name),
            call(added_entry_language, added_entry_name),
        ])
        m_retriever.get_translations.assert_called_once_with(entry_language, entry_name)
        assert 2 == len(resource.links)
        link_nl = resource.links.difference({link_en}).pop()
        assert 'Amsterdam' == link_nl.label
        assert 'nl' == link_nl.locale
        assert MediaType('text/html') == link_nl.media_type
        assert link_nl.description is not None
        assert 'external' == link_nl.relationship


class TestWikipedia:
    @patch_cache
    def test_filter(self, aioresponses: aioresponses) -> None:
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

        with App() as app:
            app.project.configuration.extensions.append(ExtensionConfiguration(Wikipedia))
            actual = app.jinja2_environment.from_string(
                '{% for entry in (links | wikipedia) %}{{ entry.content }}{% endfor %}').render(links=links)
        assert extract == actual

    @patch_cache
    async def test_post_load(self, aioresponses: aioresponses) -> None:
        resource = Source('the_source', 'The Source')
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

        with App() as app:
            app.project.configuration.extensions.append(ExtensionConfiguration(Wikipedia))
            app.project.ancestry.entities.append(resource)
            await load(app)

        assert 1 == len(resource.links)
        assert entry_title == link.label
        assert 'en' == link.locale
        assert MediaType('text/html') == link.media_type
        assert link.description is not None
        assert 'external' == link.relationship
