from os.path import exists, join, dirname
from tempfile import TemporaryDirectory
from unittest import TestCase

from parameterized import parameterized

from betty.ancestry import File
from betty.config import Configuration
from betty.jinja2 import create_environment
from betty.plugin import Plugin
from betty.site import Site


class FlattenTest(TestCase):
    @parameterized.expand([
        ('', '{{ [] | flatten | join(", ") }}'),
        ('', '{{ [[], [], []] | flatten | join(", ") }}'),
        ('kiwi, apple, banana',
         '{{ [["kiwi"], ["apple"], ["banana"]] | flatten | join(", ") }}'),
    ])
    def test(self, expected, template):
        with TemporaryDirectory() as www_directory_path:
            environment = create_environment(
                Site(Configuration(www_directory_path, 'https://example.com')))
            self.assertEquals(
                expected, environment.from_string(template).render())


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
    def test(self, expected, template, data):
        with TemporaryDirectory() as www_directory_path:
            environment = create_environment(
                Site(Configuration(www_directory_path, 'https://example.com')))
            self.assertEquals(expected, environment.from_string(
                template).render(data=data))


class ParagraphsTest(TestCase):
    @parameterized.expand([
        ('<p></p>', '{{ "" | paragraphs }}'),
        ('<p>Apples <br>\n and <br>\n oranges</p>',
         '{{ "Apples \n and \n oranges" | paragraphs }}'),
    ])
    def test(self, expected, template):
        with TemporaryDirectory() as www_directory_path:
            environment = create_environment(
                Site(Configuration(www_directory_path, 'https://example.com')))
            self.assertEquals(
                expected, environment.from_string(template).render())


class FormatDegreesTest(TestCase):
    @parameterized.expand([
        ('0° 0&#39; 0&#34;', '{{ 0 | format_degrees }}'),
        ('52° 22&#39; 1&#34;', '{{ 52.367 | format_degrees }}'),
    ])
    def test(self, expected, template):
        with TemporaryDirectory() as www_directory_path:
            environment = create_environment(
                Site(Configuration(www_directory_path, 'https://example.com')))
            self.assertEquals(
                expected, environment.from_string(template).render())


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
    def test(self, expected, template, data):
        with TemporaryDirectory() as www_directory_path:
            environment = create_environment(
                Site(Configuration(www_directory_path, 'https://example.com')))
            self.assertEquals(expected, environment.from_string(
                template).render(data=data))


class TakewhileTest(TestCase):
    @parameterized.expand([
        ('', '{{ [] | takewhile("ne", None) | join(", ") }}'),
        ('kiwi, apple',
         '{{ ["kiwi", "apple", None, "banana", None] | takewhile | join(", ") }}'),
        ('kiwi, apple',
         '{{ ["kiwi", "apple", None, "banana", None] | takewhile("ne", None) | join(", ") }}'),
    ])
    def test(self, expected, template):
        with TemporaryDirectory() as www_directory_path:
            environment = create_environment(
                Site(Configuration(www_directory_path, 'https://example.com')))
            self.assertEquals(
                expected, environment.from_string(template).render())


class FileTest(TestCase):
    @parameterized.expand([
        ('/file/F1.py', '{{ file | file }}', File('F1', __file__)),
        ('/file/F1.py:/file/F1.py',
         '{{ file | file }}:{{ file | file }}', File('F1', __file__)),
    ])
    def test(self, expected, template, file):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            environment = create_environment(Site(configuration))
            actual = environment.from_string(template).render(file=file)
            self.assertEquals(expected, actual)
            for file_path in actual.split(':'):
                self.assertTrue(
                    exists(join(configuration.www_directory_path, file_path[1:])))


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
    def test(self, expected, template, file):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            environment = create_environment(Site(configuration))
            actual = environment.from_string(template).render(file=file)
            self.assertEquals(expected, actual)
            for file_path in actual.split(':'):
                self.assertTrue(
                    exists(join(configuration.www_directory_path, file_path[1:])))


class TestPlugin(Plugin):
    pass


class PluginsTest(TestCase):
    def test_with_unknown_plugin_module(self):
        with TemporaryDirectory() as www_directory_path:
            environment = create_environment(
                Site(Configuration(www_directory_path, 'https://example.com')))
            template = '{%- if "betty.UnknownModule.Plugin" in plugins %}true{% else %}false{% endif %}'
            self.assertEquals(
                'false', environment.from_string(template).render())

    def test_with_unknown_plugin_class(self):
        with TemporaryDirectory() as www_directory_path:
            environment = create_environment(
                Site(Configuration(www_directory_path, 'https://example.com')))
            template = '{%- if "betty.UnknownPlugin" in plugins %}true{% else %}false{% endif %}'
            self.assertEquals(
                'false', environment.from_string(template).render())

    def test_with_disabled_plugin(self):
        with TemporaryDirectory() as www_directory_path:
            environment = create_environment(
                Site(Configuration(www_directory_path, 'https://example.com')))
            template = '{%- if "' + TestPlugin.__module__ + \
                '.TestPlugin" in plugins %}true{% else %}false{% endif %}'
            self.assertEquals(
                'false', environment.from_string(template).render())

    def test_with_enabled_plugin(self):
        with TemporaryDirectory() as www_directory_path:
            configuration = Configuration(
                www_directory_path, 'https://example.com')
            configuration.plugins[TestPlugin] = {}
            environment = create_environment(Site(configuration))
            template = '{%- if "' + TestPlugin.__module__ + \
                '.TestPlugin" in plugins %}true{% else %}false{% endif %}'
            self.assertEquals(
                'true', environment.from_string(template).render())
