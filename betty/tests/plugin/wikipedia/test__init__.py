from tempfile import TemporaryDirectory
from time import sleep
from typing import Dict, List
from unittest import TestCase
from unittest.mock import patch

import requests_mock
from parameterized import parameterized
from requests import RequestException

from betty.ancestry import Link
from betty.config import Configuration
from betty.jinja2 import create_environment
from betty.plugin.wikipedia import Entry, Wikipedia, Retriever
from betty.site import Site


class EntryTest(TestCase):
    def test_uri(self):
        uri = 'https://en.wikipedia.org/wiki/Amsterdam'
        sut = Entry(uri, 'Title for Amsterdam', 'Content for Amsterdam')
        self.assertEquals(uri, sut.uri)

    def test_title(self):
        title = 'Amsterdam'
        sut = Entry('https://en.wikipedia.org/wiki/UriForAmsterdam',
                    title, 'Content for Amsterdam')
        self.assertEquals(title, sut.title)

    def test_content(self):
        content = 'Amsterdam'
        sut = Entry('https://en.wikipedia.org/wiki/UriForAmsterdam',
                    'Title for Amsterdam', content)
        self.assertEquals(content, sut.content)


class RetrieverTest(TestCase):
    @parameterized.expand([
        ('https://en.wikipedia.org/wiki/Amsterdam',),
        ('http://en.wikipedia.org/wiki/Amsterdam',),
    ])
    @requests_mock.mock()
    def test_one_should_return_entry(self, page_uri: str, m_requests):
        language = 'en'
        link = Link(page_uri)
        api_uri = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=extracts&exintro&format=json&formatversion=2'
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
        m_requests.get(api_uri, [
            {
                'json': api_response_body_1,
            },
            {
                'exc': RequestException,
            },
            {
                'json': api_response_body_4,
            },
        ])
        with TemporaryDirectory() as cache_directory_path:
            retriever = Retriever(cache_directory_path, 1)
            # The first retrieval should make a successful request and set the cache.
            entry_1 = retriever.one(language, link)
            # The second retrieval should hit the cache from the first request.
            entry_2 = retriever.one(language, link)
            # The third retrieval should result in a failed request, and hit the cache from the first request.
            sleep(2)
            entry_3 = retriever.one(language, link)
            # The fourth retrieval should make a successful request and set the cache again.
            entry_4 = retriever.one(language, link)
            # The fifth retrieval should hit the cache from the fourth request.
            entry_5 = retriever.one(language, link)
        self.assertEquals(3, m_requests.call_count)
        for entry in [entry_1, entry_2, entry_3]:
            self.assertEquals(page_uri, entry.uri)
            self.assertEquals(title, entry.title)
            self.assertEquals(extract_1, entry.content)
        for entry in [entry_4, entry_5]:
            self.assertEquals(page_uri, entry.uri)
            self.assertEquals(title, entry.title)
            self.assertEquals(extract_4, entry.content)

    @requests_mock.mock()
    def test_one_should_return_translated_entry(self, m_requests):
        language = 'nl'
        page_uri = 'https://en.wikipedia.org/wiki/Amsterdam'
        link = Link(page_uri)
        translations_api_uri = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=langlinks&lllimit=500&format=json&formatversion=2'
        page_api_uri = 'https://nl.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=extracts&exintro&format=json&formatversion=2'
        title = 'Amsterdam'
        extract_nl = 'De hoofdstad van Nederland.'
        api_translations_response_body_nl = {
            'query': {
                'pages': [
                    {
                        'langlinks': [
                            {
                                'lang': 'nl',
                                'title': title,
                            },
                        ],
                    },
                ],
            },
        }
        api_page_response_body_nl = {
            'query': {
                'pages': [
                    {
                        'title': title,
                        'extract': extract_nl,
                    },
                ],
            }
        }
        m_requests.register_uri(
            'GET', translations_api_uri, json=api_translations_response_body_nl)
        m_requests.register_uri('GET', page_api_uri,
                                json=api_page_response_body_nl)
        with TemporaryDirectory() as cache_directory_path:
            retriever = Retriever(cache_directory_path, 1)
            entry = retriever.one(language, link)
        self.assertEquals(2, m_requests.call_count)
        self.assertEquals(page_uri, entry.uri)
        self.assertEquals(title, entry.title)
        self.assertEquals(extract_nl, entry.content)

    @parameterized.expand([
        ([],),
        ([
            {
                'lang': 'de',
                'tilte': 'Amsterdam',
            },
        ],),
    ])
    @requests_mock.mock()
    def test_one_should_return_none_if_no_translation_exists(self, langlinks: List[Dict], m_requests):
        language = 'nl'
        page_uri = 'https://en.wikipedia.org/wiki/Amsterdam'
        link = Link(page_uri)
        translations_api_uri = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=langlinks&lllimit=500&format=json&formatversion=2'
        api_translations_response_body_nl = {
            'query': {
                'pages': [
                    {
                        'langlinks': langlinks,
                    },
                ],
            },
        }
        m_requests.register_uri(
            'GET', translations_api_uri, json=api_translations_response_body_nl)
        with TemporaryDirectory() as cache_directory_path:
            retriever = Retriever(cache_directory_path, 1)
            entry = retriever.one(language, link)
        self.assertEquals(1, m_requests.call_count)
        self.assertIsNone(entry)

    @parameterized.expand([
        ('',),
        ('127.0.0.1',),
        ('localhost',),
        ('https://wikipedia.org/wiki/',),
        ('https://en.wikipedia.org',),
        ('https://en.wikipedia.org/wiki/',),
        ('https://ancestry.bartfeenstra.com',),
    ])
    @requests_mock.mock()
    def test_one_should_ignore_unsupported_uris(self, page_uri: str, m_requests):
        language = 'uk'
        link = Link(page_uri)
        with TemporaryDirectory() as cache_directory_path:
            entry = Retriever(cache_directory_path).one(language, link)
        self.assertIsNone(entry)
        self.assertEquals(0, len(m_requests.request_history))

    @requests_mock.mock()
    @patch('sys.stderr')
    def test_one_should_handle_request_errors(self, m_requests, _):
        language = 'en'
        page_uri = 'https://en.wikipedia.org/wiki/Amsterdam'
        link = Link(page_uri)
        api_uri = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=extracts&exintro&format=json&formatversion=2'
        m_requests.register_uri('GET', api_uri, exc=RequestException)
        with TemporaryDirectory() as cache_directory_path:
            entry = Retriever(cache_directory_path).one(language, link)
        self.assertIsNone(entry)

    @parameterized.expand([
        ('https://en.wikipedia.org/wiki/Amsterdam',),
        ('http://en.wikipedia.org/wiki/Amsterdam',),
    ])
    @requests_mock.mock()
    def test_all_should_return_entry(self, page_uri: str, m_requests):
        language = 'en'
        link = Link(page_uri)
        api_uri = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=extracts&exintro&format=json&formatversion=2'
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
        m_requests.register_uri('GET', api_uri, json=api_response_body)
        with TemporaryDirectory() as cache_directory_path:
            entries = list(
                Retriever(cache_directory_path).all(language, [link]))
        self.assertEquals(1, len(entries))
        entry = entries[0]
        self.assertEquals(page_uri, entry.uri)
        self.assertEquals(title, entry.title)
        self.assertEquals(extract, entry.content)


class WikipediaTest(TestCase):
    @patch('os.path.expanduser')
    @requests_mock.mock()
    def test_filter(self, m_expanduser, m_requests):
        with TemporaryDirectory() as cache_directory_path:
            m_expanduser.side_effect = lambda _: cache_directory_path
            with TemporaryDirectory() as output_directory_path:
                configuration = Configuration(
                    output_directory_path, 'https://ancestry.example.com')
                configuration.plugins[Wikipedia] = {}

                environment = create_environment(Site(configuration))
                page_uri = 'https://en.wikipedia.org/wiki/Amsterdam'
                link = Link(page_uri)
                api_uri = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=extracts&exintro&format=json&formatversion=2'
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
                m_requests.register_uri('GET', api_uri, json=api_response_body)
                actual = environment.from_string(
                    '{% for entry in ([link] | wikipedia) %}{{ entry.content }}{% endfor %}').render(link=link)
                self.assertEquals(extract, actual)
