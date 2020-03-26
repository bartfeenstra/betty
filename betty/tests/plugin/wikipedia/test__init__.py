from tempfile import TemporaryDirectory
from time import sleep
from typing import Tuple, Optional
from unittest import TestCase
from unittest.mock import patch, call

import requests_mock
from parameterized import parameterized
from requests import RequestException

from betty.ancestry import Ancestry, Source, IdentifiableCitation, IdentifiableSource, Link
from betty.config import Configuration, LocaleConfiguration
from betty.jinja2 import create_environment
from betty.parse import parse
from betty.plugin.wikipedia import Entry, Retriever, NotAnEntryError, parse_url, RetrievalError, Populator, Wikipedia
from betty.site import Site


class ParseUrlTest(TestCase):
    @parameterized.expand([
        (('en', 'Amsterdam'), 'http://en.wikipedia.org/wiki/Amsterdam',),
        (('nl', 'Amsterdam'), 'https://nl.wikipedia.org/wiki/Amsterdam',),
        (('en', 'Amsterdam'), 'http://en.wikipedia.org/wiki/Amsterdam',),
        (('en', 'Amsterdam'), 'https://en.wikipedia.org/wiki/Amsterdam/',),
        (('en', 'Amsterdam'), 'https://en.wikipedia.org/wiki/Amsterdam/some-path',),
        (('en', 'Amsterdam'), 'https://en.wikipedia.org/wiki/Amsterdam?some=query',),
        (('en', 'Amsterdam'), 'https://en.wikipedia.org/wiki/Amsterdam#some-fragment',),
    ])
    def test_should_return(self, expected: Tuple[str, str], url: str) -> None:
        self.assertEquals(expected, parse_url(url))

    @parameterized.expand([
        ('',),
        ('ftp://en.wikipedia.org/wiki/Amsterdam',),
        ('https://en.wikipedia.org/w/index.php?title=Amsterdam&action=edit',),
    ])
    def test_should_error(self, url: str) -> None:
        with self.assertRaises(NotAnEntryError):
            parse_url(url)


class EntryTest(TestCase):
    def test_url(self) -> None:
        sut = Entry('nl', 'Amsterdam', 'Title for Amsterdam', 'Content for Amsterdam')
        self.assertEquals('https://nl.wikipedia.org/wiki/Amsterdam', sut.url)

    def test_title(self) -> None:
        title = 'Title for Amsterdam'
        sut = Entry('nl', 'Amsterdam', title, 'Content for Amsterdam')
        self.assertEquals(title, sut.title)

    def test_content(self) -> None:
        content = 'Content for Amsterdam'
        sut = Entry('nl', 'Amsterdam', 'Title for Amsterdam', content)
        self.assertEquals(content, sut.content)


class RetrieverTest(TestCase):
    @parameterized.expand([
        ([], {},),
        ([
            ('nl', 'Amsterdam'),
            ('uk', 'Амстердам'),
        ], {
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
    @requests_mock.mock()
    @patch('sys.stderr')
    def test_get_translations_should_return(self, expected, response_pages_json, m_stderr, m_requests) -> None:
        entry_language = 'en'
        entry_name = 'Amsterdam'
        api_url = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=langlinks&lllimit=500&format=json&formatversion=2' % (entry_language, entry_name)
        api_response_body = {
            'query': {
                'pages': [response_pages_json],
            },
        }
        m_requests.register_uri('GET', api_url, json=api_response_body)
        with TemporaryDirectory() as cache_directory_path:
            translations = Retriever(cache_directory_path).get_translations(entry_language, entry_name)
        self.assertEqual(expected, translations)

    @requests_mock.mock()
    @patch('sys.stderr')
    def test_get_translations_with_request_error_should_raise_retrieval_error(self, m_requests, m_stderr) -> None:
        entry_language = 'en'
        entry_name = 'Amsterdam'
        api_url = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=langlinks&lllimit=500&format=json&formatversion=2' % (entry_language, entry_name)
        m_requests.register_uri('GET', api_url, exc=RequestException)
        with TemporaryDirectory() as cache_directory_path:
            with self.assertRaises(RetrievalError):
                Retriever(cache_directory_path).get_translations(entry_language, entry_name)

    @requests_mock.mock()
    @patch('sys.stderr')
    def test_get_translations_with_invalid_json_response_should_raise_retrieval_error(self, m_requests, m_stderr) -> None:
        entry_language = 'en'
        entry_name = 'Amsterdam'
        api_url = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=langlinks&lllimit=500&format=json&formatversion=2' % (entry_language, entry_name)
        m_requests.register_uri('GET', api_url, text='{Haha Im not rly JSON}')
        with TemporaryDirectory() as cache_directory_path:
            with self.assertRaises(RetrievalError):
                Retriever(cache_directory_path).get_translations(entry_language, entry_name)

    @parameterized.expand([
        ({},),
        ({
            'query': {}
        },),
        ({
            'query': {
                'pages': {}
            }
        },),
        ({
            'query': {
                'pages': []
            }
        },),
    ])
    @requests_mock.mock()
    @patch('sys.stderr')
    def test_get_translations_with_unexpected_json_response_should_raise_retrieval_error(self, response_json, m_stderr, m_requests) -> None:
        entry_language = 'en'
        entry_name = 'Amsterdam'
        api_url = 'https://%s.wikipedia.org/w/api.php?action=query&titles=%s&prop=langlinks&lllimit=500&format=json&formatversion=2' % (entry_language, entry_name)
        m_requests.register_uri('GET', api_url, json=response_json)
        with TemporaryDirectory() as cache_directory_path:
            with self.assertRaises(RetrievalError):
                Retriever(cache_directory_path).get_translations(entry_language, entry_name)

    @requests_mock.mock()
    def test_get_entry_should_return(self, m_requests) -> None:
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
        m_requests.get(api_url, [
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
            entry_1 = retriever.get_entry(entry_language, entry_name)
            # The second retrieval should hit the cache from the first request.
            entry_2 = retriever.get_entry(entry_language, entry_name)
            # The third retrieval should result in a failed request, and hit the cache from the first request.
            sleep(2)
            entry_3 = retriever.get_entry(entry_language, entry_name)
            # The fourth retrieval should make a successful request and set the cache again.
            entry_4 = retriever.get_entry(entry_language, entry_name)
            # The fifth retrieval should hit the cache from the fourth request.
            entry_5 = retriever.get_entry(entry_language, entry_name)
        self.assertEquals(3, m_requests.call_count)
        for entry in [entry_1, entry_2, entry_3]:
            self.assertEquals(entry_url, entry.url)
            self.assertEquals(title, entry.title)
            self.assertEquals(extract_1, entry.content)
        for entry in [entry_4, entry_5]:
            self.assertEquals(entry_url, entry.url)
            self.assertEquals(title, entry.title)
            self.assertEquals(extract_4, entry.content)

    @requests_mock.mock()
    @patch('sys.stderr')
    def test_get_entry_with_request_error_should_raise_retrieval_error(self, m_requests, m_stderr) -> None:
        entry_language = 'en'
        entry_name = 'Amsterdam'
        api_url = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=extracts&exintro&format=json&formatversion=2'
        m_requests.register_uri('GET', api_url, exc=RequestException)
        with TemporaryDirectory() as cache_directory_path:
            with self.assertRaises(RetrievalError):
                Retriever(cache_directory_path).get_entry(entry_language, entry_name)


class PopulatorTest(TestCase):
    @patch('betty.plugin.wikipedia.Retriever')
    def test_populate_link_should_convert_http_to_https(self, m_retriever) -> None:
        sut = Populator(m_retriever)
        link = Link('http://en.wikipedia.org/wiki/Amsterdam')
        entry_language = 'nl'
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as cache_directory_path:
                configuration = Configuration(
                    output_directory_path, 'https://example.com')
                configuration.cache_directory_path = cache_directory_path
                with Site(configuration) as site:
                    sut.populate_link(link, site, entry_language)
        self.assertEqual('https://en.wikipedia.org/wiki/Amsterdam', link.url)

    @parameterized.expand([
        ('text/plain', 'text/plain'),
        ('text/html', 'text/html'),
        ('text/html', None),
    ])
    @patch('betty.plugin.wikipedia.Retriever')
    def test_populate_link_should_set_media_type(self, expected: str, media_type: Optional[str], m_retriever) -> None:
        sut = Populator(m_retriever)
        link = Link('http://en.wikipedia.org/wiki/Amsterdam')
        link.media_type = media_type
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as cache_directory_path:
                configuration = Configuration(
                    output_directory_path, 'https://example.com')
                configuration.cache_directory_path = cache_directory_path
                with Site(configuration) as site:
                    sut.populate_link(link, site, 'en')
        self.assertEqual(expected, link.media_type)

    @parameterized.expand([
        ('alternate', 'alternate'),
        ('external', 'external'),
        ('external', None),
    ])
    @patch('betty.plugin.wikipedia.Retriever')
    def test_populate_link_should_set_relationship(self, expected: str, relationship: Optional[str], m_retriever) -> None:
        sut = Populator(m_retriever)
        link = Link('http://en.wikipedia.org/wiki/Amsterdam')
        link.relationship = relationship
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as cache_directory_path:
                configuration = Configuration(
                    output_directory_path, 'https://example.com')
                configuration.cache_directory_path = cache_directory_path
                with Site(configuration) as site:
                    sut.populate_link(link, site, 'en')
        self.assertEqual(expected, link.relationship)

    @parameterized.expand([
        ('nl-NL', 'nl', 'nl-NL'),
        ('nl', 'nl', None),
        ('nl', 'en', 'nl'),
    ])
    @patch('betty.plugin.wikipedia.Retriever')
    def test_populate_link_should_set_locale(self, expected: str, entry_language: str, locale: Optional[str], m_retriever) -> None:
        sut = Populator(m_retriever)
        link = Link('http://%s.wikipedia.org/wiki/Amsterdam' % entry_language)
        link.locale = locale
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as cache_directory_path:
                configuration = Configuration(
                    output_directory_path, 'https://example.com')
                configuration.cache_directory_path = cache_directory_path
                with Site(configuration) as site:
                    sut.populate_link(link, site, entry_language)
        self.assertEqual(expected, link.locale)

    @parameterized.expand([
        ('This is the original description', 'This is the original description'),
        ('Read more on Wikipedia.', None),
    ])
    @patch('betty.plugin.wikipedia.Retriever')
    def test_populate_link_should_set_description(self, expected: str, description: str, m_retriever) -> None:
        sut = Populator(m_retriever)
        link = Link('http://en.wikipedia.org/wiki/Amsterdam')
        link.description = description
        entry_language = 'en'
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as cache_directory_path:
                configuration = Configuration(
                    output_directory_path, 'https://example.com')
                configuration.cache_directory_path = cache_directory_path
                with Site(configuration) as site:
                    sut.populate_link(link, site, entry_language)
        self.assertEqual(expected, link.description)

    @parameterized.expand([
        ('Amsterdam', 'Amsterdam'),
        ('The city of Amsterdam', None),
    ])
    @patch('betty.plugin.wikipedia.Retriever')
    def test_populate_link_should_set_label(self, expected: str, label: Optional[str], m_retriever) -> None:
        sut = Populator(m_retriever)
        link = Link('http://en.wikipedia.org/wiki/Amsterdam')
        link.label = label
        entry = Entry('en', 'The_city_of_Amsterdam', 'The city of Amsterdam', 'Amsterdam, such a lovely place!')
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as cache_directory_path:
                configuration = Configuration(
                    output_directory_path, 'https://example.com')
                configuration.cache_directory_path = cache_directory_path
                with Site(configuration) as site:
                    sut.populate_link(link, site, 'en', entry)
        self.assertEqual(expected, link.label)

    @patch('betty.plugin.wikipedia.Retriever')
    def test_populate_should_ignore_resource_without_link_support(self, m_retriever) -> None:
        source = Source('The Source')
        resource = IdentifiableCitation('the_citation', source)
        ancestry = Ancestry()
        ancestry.citations[resource.id] = resource
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as cache_directory_path:
                configuration = Configuration(
                    output_directory_path, 'https://example.com')
                configuration.cache_directory_path = cache_directory_path
                with Site(configuration) as site:
                    sut = Populator(m_retriever)
                sut.populate(ancestry, site)

    @patch('betty.plugin.wikipedia.Retriever')
    def test_populate_should_ignore_resource_without_links(self, m_retriever) -> None:
        resource = IdentifiableSource('the_source', 'The Source')
        ancestry = Ancestry()
        ancestry.sources[resource.id] = resource
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as cache_directory_path:
                configuration = Configuration(
                    output_directory_path, 'https://example.com')
                configuration.cache_directory_path = cache_directory_path
                with Site(configuration) as site:
                    sut = Populator(m_retriever)
                    sut.populate(ancestry, site)
        self.assertSetEqual(set(), resource.links)

    @patch('betty.plugin.wikipedia.Retriever')
    def test_populate_should_ignore_non_wikipedia_links(self, m_retriever) -> None:
        link = Link('https://example.com')
        resource = IdentifiableSource('the_source', 'The Source')
        resource.links.add(link)
        ancestry = Ancestry()
        ancestry.sources[resource.id] = resource
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as cache_directory_path:
                configuration = Configuration(
                    output_directory_path, 'https://example.com')
                configuration.cache_directory_path = cache_directory_path
                with Site(configuration) as site:
                    sut = Populator(m_retriever)
                    sut.populate(ancestry, site)
        self.assertSetEqual({link}, resource.links)

    @patch('betty.plugin.wikipedia.Retriever')
    def test_populate_should_populate_existing_link(self, m_retriever) -> None:
        entry_language = 'en'
        entry_name = 'Amsterdam'
        entry_title = 'Amsterdam'
        entry_content = 'Capitol of the Netherlands'
        entry = Entry(entry_language, entry_name, entry_title, entry_content)
        m_retriever.get_entry.return_value = entry

        resource = IdentifiableSource('the_source', 'The Source')
        link = Link('https://en.wikipedia.org/wiki/Amsterdam')
        resource.links.add(link)
        ancestry = Ancestry()
        ancestry.sources[resource.id] = resource
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as cache_directory_path:
                configuration = Configuration(
                    output_directory_path, 'https://example.com')
                configuration.cache_directory_path = cache_directory_path
                with Site(configuration) as site:
                    sut = Populator(m_retriever)
                    sut.populate(ancestry, site)
        m_retriever.get_entry.assert_called_once_with(entry_language, entry_name)
        self.assertEqual(1, len(resource.links))
        self.assertEqual('Amsterdam', link.label)
        self.assertEqual('en', link.locale)
        self.assertEqual('text/html', link.media_type)
        self.assertIsNotNone(link.description)
        self.assertEqual('external', link.relationship)

    @patch('betty.plugin.wikipedia.Retriever')
    def test_populate_should_add_translation_links(self, m_retriever) -> None:
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

        m_retriever.get_translations.return_value = [
            (entry_language, entry_name),
            (added_entry_language, added_entry_name),
        ]

        resource = IdentifiableSource('the_source', 'The Source')
        link_en = Link('https://en.wikipedia.org/wiki/Amsterdam')
        resource.links.add(link_en)
        ancestry = Ancestry()
        ancestry.sources[resource.id] = resource
        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as cache_directory_path:
                configuration = Configuration(
                    output_directory_path, 'https://example.com')
                configuration.cache_directory_path = cache_directory_path
                configuration.locales.clear()
                configuration.locales['en-US'] = LocaleConfiguration('en-US', 'en')
                configuration.locales['nl-NL'] = LocaleConfiguration('nl-NL', 'nl')
                with Site(configuration) as site:
                    sut = Populator(m_retriever)
                    sut.populate(ancestry, site)

        m_retriever.get_entry.assert_has_calls([
            call(entry_language, entry_name),
            call(added_entry_language, added_entry_name),
        ])
        m_retriever.get_translations.assert_called_once_with(entry_language, entry_name)
        self.assertEqual(2, len(resource.links))
        link_nl = resource.links.difference({link_en}).pop()
        self.assertEqual('Amsterdam', link_nl.label)
        self.assertEqual('nl', link_nl.locale)
        self.assertEqual('text/html', link_nl.media_type)
        self.assertIsNotNone(link_nl.description)
        self.assertEqual('external', link_nl.relationship)


class WikipediaTest(TestCase):
    @requests_mock.mock()
    def test_filter(self, m_requests) -> None:
        entry_url = 'https://en.wikipedia.org/wiki/Amsterdam'
        links = [
            Link(entry_url),
            # Add a link to Wikipedia, but using a locale that's not used by the site, to test it's ignored.
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
        m_requests.register_uri('GET', api_url, json=api_response_body)

        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as cache_directory_path:
                configuration = Configuration(
                    output_directory_path, 'https://ancestry.example.com')
                configuration.cache_directory_path = cache_directory_path
                configuration.plugins[Wikipedia] = {}

                environment = create_environment(Site(configuration))
                actual = environment.from_string(
                    '{% for entry in (links | wikipedia) %}{{ entry.content }}{% endfor %}').render(links=links)
        self.assertEquals(extract, actual)

    @requests_mock.mock()
    def test_post_parse(self, m_requests) -> None:
        resource = IdentifiableSource('the_source', 'The Source')
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
        m_requests.register_uri('GET', entry_api_url, json=entry_api_response_body)
        translations_api_response_body = {
            'query': {
                'pages': [
                    {
                        'langlinks': [],
                    },
                ],
            },
        }
        translations_api_url = 'https://en.wikipedia.org/w/api.php?action=query&titles=Amsterdam&prop=langlinks&lllimit=500&format=json&formatversion=2'
        m_requests.register_uri('GET', translations_api_url, json=translations_api_response_body)

        with TemporaryDirectory() as output_directory_path:
            with TemporaryDirectory() as cache_directory_path:
                configuration = Configuration(
                    output_directory_path, 'https://example.com')
                configuration.cache_directory_path = cache_directory_path
                configuration.plugins[Wikipedia] = {}
                with Site(configuration) as site:
                    site.ancestry.sources[resource.id] = resource
                    parse(site)

        self.assertEqual(1, len(resource.links))
        self.assertEqual(entry_title, link.label)
        self.assertEqual('en', link.locale)
        self.assertEqual('text/html', link.media_type)
        self.assertIsNotNone(link.description)
        self.assertEqual('external', link.relationship)
