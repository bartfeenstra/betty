from os.path import exists, join, dirname
from tempfile import TemporaryDirectory
from typing import List
from unittest import TestCase

from parameterized import parameterized

from betty.ancestry import File, LocalizedName
from betty.config import Configuration, LocaleConfiguration
from betty.functools import sync
from betty.jinja2 import create_environment
from betty.locale import Date
from betty.plugin import Plugin
from betty.site import Site


class FlattenTest(TestCase):
    @parameterized.expand([
        ('', '{{ [] | flatten | join(", ") }}'),
        ('', '{{ [[], [], []] | flatten | join(", ") }}'),
        ('kiwi, apple, banana',
         '{{ [["kiwi"], ["apple"], ["banana"]] | flatten | join(", ") }}'),
    ])
    @sync
    async def test(self, expected, template):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                self.assertEquals(expected, await site.jinja2_environment.from_string(template).render_async())


class WalkData:
    def __init__(self, label, children=None):
        self._label = label
        self.children = children or []

    def __str__(self):
        return self._label


class WalkTest(TestCase):
    @parameterized.expand([
        ('', '{{ data | walk("children") | join }}', WalkData('parent')),
        ('child1, child1child1, child2', '{{ data | walk("children") | join(", ") }}',
         WalkData('parent', [WalkData('child1', [WalkData('child1child1')]), WalkData('child2')])),
    ])
    @sync
    async def test(self, expected, template, data):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                self.assertEquals(expected, await site.jinja2_environment.from_string(template).render_async(data=data))


class ParagraphsTest(TestCase):
    @parameterized.expand([
        ('<p></p>', '{{ "" | paragraphs }}'),
        ('<p>Apples <br>\n and <br>\n oranges</p>',
         '{{ "Apples \n and \n oranges" | paragraphs }}'),
    ])
    @sync
    async def test(self, expected, template):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                self.assertEquals(
                    expected, await site.jinja2_environment.from_string(template).render_async())


class FormatDegreesTest(TestCase):
    @parameterized.expand([
        ('0° 0&#39; 0&#34;', '{{ 0 | format_degrees }}'),
        ('52° 22&#39; 1&#34;', '{{ 52.367 | format_degrees }}'),
    ])
    @sync
    async def test(self, expected, template):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                self.assertEquals(expected, await site.jinja2_environment.from_string(template).render_async())


class MapData:
    def __init__(self, label):
        self.label = label


class MapTest(TestCase):
    @parameterized.expand([
        ('kiwi, apple, banana', '{{ data | map(attribute="label") | join(", ") }}',
         [MapData('kiwi'), MapData('apple'), MapData('banana')]),
        ('kiwi, None, apple, None, banana',
         '{% macro print_string(value) %}{% if value is none %}None{% else %}{{ value }}{% endif %}{% endmacro %}{{ ["kiwi", None, "apple", None, "banana"] | map(print_string) | join(", ") }}',
         {}),
    ])
    @sync
    async def test(self, expected, template, data):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                self.assertEquals(expected, await site.jinja2_environment.from_string(template).render_async(data=data))


class TakewhileTest(TestCase):
    @parameterized.expand([
        ('', '{{ [] | takewhile("ne", None) | join(", ") }}'),
        ('kiwi, apple',
         '{{ ["kiwi", "apple", None, "banana", None] | takewhile | join(", ") }}'),
        ('kiwi, apple',
         '{{ ["kiwi", "apple", None, "banana", None] | takewhile("ne", None) | join(", ") }}'),
    ])
    @sync
    async def test(self, expected, template):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                self.assertEquals(expected, await site.jinja2_environment.from_string(template).render_async())


class FileTest(TestCase):
    @parameterized.expand([
        ('/file/F1.py', '{{ file | file }}', File('F1', __file__)),
        ('/file/F1.py:/file/F1.py',
         '{{ file | file }}:{{ file | file }}', File('F1', __file__)),
    ])
    @sync
    async def test(self, expected, template, file):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                actual = await site.jinja2_environment.from_string(template).render_async(file=file)
                self.assertEquals(expected, actual)
                for file_path in actual.split(':'):
                    self.assertTrue(exists(join(site.configuration.www_directory_path, file_path[1:])))


image_path = join(dirname(dirname(__file__)), 'resources',
                  'public', 'static', 'betty-512x512.png')


class ImageTest(TestCase):
    @parameterized.expand([
        ('/file/F1-99x-.png',
         '{{ file | image(width=99) }}', File('F1', image_path)),
        ('/file/F1--x99.png',
         '{{ file | image(height=99) }}', File('F1', image_path)),
        ('/file/F1-99x99.png',
         '{{ file | image(width=99, height=99) }}', File('F1', image_path)),
        ('/file/F1-99x99.png:/file/F1-99x99.png',
         '{{ file | image(width=99, height=99) }}:{{ file | image(width=99, height=99) }}', File('F1', image_path)),
    ])
    @sync
    async def test(self, expected, template, file):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                actual = await site.jinja2_environment.from_string(template).render_async(file=file)
                self.assertEquals(expected, actual)
                for file_path in actual.split(':'):
                    self.assertTrue(
                        exists(join(site.configuration.www_directory_path, file_path[1:])))


class TestPlugin(Plugin):
    pass


class PluginsTest(TestCase):
    @sync
    async def test_with_unknown_plugin_module(self):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                template = '{% if "betty.UnknownModule.Plugin" in plugins %}true{% else %}false{% endif %}'
                self.assertEquals('false', await site.jinja2_environment.from_string(template).render_async())

    @sync
    async def test_with_unknown_plugin_class(self):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                template = '{% if "betty.UnknownPlugin" in plugins %}true{% else %}false{% endif %}'
                self.assertEquals('false', await site.jinja2_environment.from_string(template).render_async())

    @sync
    async def test_with_disabled_plugin(self):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                template = '{% if "' + TestPlugin.__module__ + \
                    '.TestPlugin" in plugins %}true{% else %}false{% endif %}'
                self.assertEquals('false', await site.jinja2_environment.from_string(template).render_async())

    @sync
    async def test_with_enabled_plugin(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[TestPlugin] = {}
            async with Site(configuration) as site:
                template = '{% if "' + TestPlugin.__module__ + \
                    '.TestPlugin" in plugins %}true{% else %}false{% endif %}'
                self.assertEquals('true', await site.jinja2_environment.from_string(template).render_async())


class FormatDateTest(TestCase):
    @sync
    async def test(self):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                environment = create_environment(site)
                template = '{{ date | format_date }}'
                date = Date(1970, 1, 1)
                self.assertEquals('January 1, 1970', await environment.from_string(template).render_async(date=date))


class SortLocalizedsTest(TestCase):
    class WithLocalizedNames:
        def __init__(self, identifier, names: List[LocalizedName]):
            self.id = identifier
            self.names = names

        def __repr__(self):
            return self.id

    @sync
    async def test(self):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                template = '{{ data | sort_localizeds(localized_attribute="names", sort_attribute="name") }}'
                data = [
                    self.WithLocalizedNames('third', [
                        LocalizedName('3', 'nl-NL'),
                    ]),
                    self.WithLocalizedNames('second', [
                        LocalizedName('2', 'en'),
                        LocalizedName('1', 'nl-NL'),
                    ]),
                    self.WithLocalizedNames('first', [
                        LocalizedName('2', 'nl-NL'),
                        LocalizedName('1', 'en-US'),
                    ]),
                ]
                self.assertEquals('[first, second, third]', await site.jinja2_environment.from_string(template).render_async(data=data))

    @sync
    async def test_with_empty_iterable(self):
        with TemporaryDirectory() as output_directory_path:
            async with Site(Configuration(output_directory_path, 'https://example.com')) as site:
                template = '{{ data | sort_localizeds(localized_attribute="names", sort_attribute="name") }}'
                data = []
                self.assertEquals('[]', await site.jinja2_environment.from_string(template).render_async(data=data))


class SelectLocalizedsTest(TestCase):
    @parameterized.expand([
        ('', 'en', []),
        ('Apple', 'en', [
            LocalizedName('Apple', 'en')
        ]),
        ('Apple', 'en', [
            LocalizedName('Apple', 'en-US')
        ]),
        ('Apple', 'en-US', [
            LocalizedName('Apple', 'en')
        ]),
        ('', 'nl', [
            LocalizedName('Apple', 'en')
        ]),
        ('', 'nl-NL', [
            LocalizedName('Apple', 'en')
        ]),
    ])
    @sync
    async def test(self, expected: str, locale: str, data):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.locales.clear()
            configuration.locales[locale] = LocaleConfiguration(locale)
            async with Site(configuration) as site:
                environment = create_environment(site)
                template = '{{ data | select_localizeds | map(attribute="name") | join(", ") }}'
                self.assertEquals(expected, await environment.from_string(template).render_async(data=data))
