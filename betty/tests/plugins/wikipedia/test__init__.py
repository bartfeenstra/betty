from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import requests_mock
from parameterized import parameterized
from requests import RequestException

from betty.ancestry import Link
from betty.config import Configuration
from betty.jinja2 import create_environment
from betty.plugins.wikipedia import _retrieve_one, Entry, _retrieve_all, Wikipedia
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


class RetrieveOneTest(TestCase):
    @parameterized.expand([
        ('https://en.wikipedia.org/wiki/Amsterdam',),
        ('http://en.wikipedia.org/wiki/Amsterdam',),
    ])
    @requests_mock.mock()
    def test_retrieve_one_should_return_entry(self, page_uri: str, m):
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
        m.register_uri('GET', api_uri, json=api_response_body)
        entry = _retrieve_one(link)
        self.assertEquals(page_uri, entry.uri)
        self.assertEquals(title, entry.title)
        self.assertEquals(extract, entry.content)

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
    def test_retrieve_one_should_ignore_unsupported_uris(self, page_uri: str, m):
        link = Link(page_uri)
        entry = _retrieve_one(link)
        self.assertIsNone(entry)
        self.assertEquals(0, len(m.request_history))

    @requests_mock.mock()
    @patch('sys.stderr')
    def test_retrieve_one_should_handle_request_errors(self, m, _):
        page_uri = 'https://en.wikipedia.org/wiki/Amsterdam'
        link = Link(page_uri)
        api_uri = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=extracts&exintro&format=json&formatversion=2'
        m.register_uri('GET', api_uri, exc=RequestException)
        entry = _retrieve_one(link)
        self.assertIsNone(entry)


class RetrieveaLLTest(TestCase):
    @parameterized.expand([
        ('https://en.wikipedia.org/wiki/Amsterdam',),
        ('http://en.wikipedia.org/wiki/Amsterdam',),
    ])
    @requests_mock.mock()
    def test_retrieve_one_should_return_entry(self, page_uri: str, m):
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
        m.register_uri('GET', api_uri, json=api_response_body)
        entries = list(_retrieve_all([link]))
        self.assertEquals(1, len(entries))
        entry = entries[0]
        self.assertEquals(page_uri, entry.uri)
        self.assertEquals(title, entry.title)
        self.assertEquals(extract, entry.content)


class WikipediaTest(TestCase):
    @requests_mock.mock()
    def test_filter(self, m):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://ancestry.example.com')
            configuration.plugins[Wikipedia] = {}

            environment = create_environment(Site(configuration))
            page_uri = 'https://en.wikipedia.org/wiki/Amsterdam'
            link = Link(page_uri)
            api_uri = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=extracts&exintro&format=json&formatversion=2'
            title = 'Amstelredam'
            extract = 'De hoofdstad vanF Nederland.'
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
            m.register_uri('GET', api_uri, json=api_response_body)
            actual = environment.from_string(
                '{% for entry in ([link] | wikipedia) %}{{ entry.content }}{% endfor %}').render(link=link)
            self.assertEquals(extract, actual)
