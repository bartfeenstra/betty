from os.path import exists, join, dirname
from typing import List, Dict, Optional, Iterable

from parameterized import parameterized

from betty.ancestry import File, PlaceName, Subject, Attendee, Witness, Dated
from betty.config import Configuration, LocaleConfiguration
from betty.functools import sync
from betty.locale import Date, Datey, DateRange, Localized
from betty.plugin import Plugin
from betty.tests import TemplateTestCase


class FlattenTest(TemplateTestCase):
    @parameterized.expand([
        ('', '{{ [] | flatten | join(", ") }}'),
        ('', '{{ [[], [], []] | flatten | join(", ") }}'),
        ('kiwi, apple, banana',
         '{{ [["kiwi"], ["apple"], ["banana"]] | flatten | join(", ") }}'),
    ])
    @sync
    async def test(self, expected, template):
        async with self._render(template_string=template) as (actual, _):
            self.assertEquals(expected, actual)


class WalkTest(TemplateTestCase):
    class WalkData:
        def __init__(self, label, children=None):
            self._label = label
            self.children = children or []

        def __str__(self):
            return self._label

    @parameterized.expand([
        ('', '{{ data | walk("children") | join }}', WalkData('parent')),
        ('child1, child1child1, child2', '{{ data | walk("children") | join(", ") }}',
         WalkData('parent', [WalkData('child1', [WalkData('child1child1')]), WalkData('child2')])),
    ])
    @sync
    async def test(self, expected, template, data):
        async with self._render(template_string=template, data={
            'data': data,
        }) as (actual, _):
            self.assertEquals(expected, actual)


class ParagraphsTest(TemplateTestCase):
    @parameterized.expand([
        ('<p></p>', '{{ "" | paragraphs }}'),
        ('<p>Apples <br>\n and <br>\n oranges</p>',
         '{{ "Apples \n and \n oranges" | paragraphs }}'),
    ])
    @sync
    async def test(self, expected, template):
        async with self._render(template_string=template) as (actual, _):
            self.assertEquals(expected, actual)


class FormatDegreesTest(TemplateTestCase):
    @parameterized.expand([
        ('0° 0&#39; 0&#34;', '{{ 0 | format_degrees }}'),
        ('52° 22&#39; 1&#34;', '{{ 52.367 | format_degrees }}'),
    ])
    @sync
    async def test(self, expected, template):
        async with self._render(template_string=template) as (actual, _):
            self.assertEquals(expected, actual)


class MapData:
    def __init__(self, label):
        self.label = label


class MapTest(TemplateTestCase):
    @parameterized.expand([
        ('kiwi, apple, banana', '{{ data | map(attribute="label") | join(", ") }}',
         [MapData('kiwi'), MapData('apple'), MapData('banana')]),
        ('kiwi, None, apple, None, banana',
         '{% macro print_string(value) %}{% if value is none %}None{% else %}{{ value }}{% endif %}{% endmacro %}{{ ["kiwi", None, "apple", None, "banana"] | map(print_string) | join(", ") }}',
         {}),
    ])
    @sync
    async def test(self, expected, template, data):
        async with self._render(template_string=template, data={
            'data': data,
        }) as (actual, _):
            self.assertEquals(expected, actual)


class SelectwhileTest(TemplateTestCase):
    @parameterized.expand([
        ('', '{{ [] | selectwhile("ne", None) | join(", ") }}'),
        ('kiwi, apple',
         '{{ ["kiwi", "apple", None, "banana", None] | selectwhile | join(", ") }}'),
        ('kiwi, apple',
         '{{ ["kiwi", "apple", None, "banana", None] | selectwhile("ne", None) | join(", ") }}'),
    ])
    @sync
    async def test(self, expected, template):
        async with self._render(template_string=template) as (actual, _):
            self.assertEquals(expected, actual)


class FileTest(TemplateTestCase):
    @parameterized.expand([
        ('/file/F1.py', '{{ file | file }}', File('F1', __file__)),
        ('/file/F1.py:/file/F1.py',
         '{{ file | file }}:{{ file | file }}', File('F1', __file__)),
    ])
    @sync
    async def test(self, expected, template, file):
        async with self._render(template_string=template, data={
            'file': file,
        }) as (actual, site):
            self.assertEquals(expected, actual)
            for file_path in actual.split(':'):
                self.assertTrue(exists(join(site.configuration.www_directory_path, file_path[1:])))


class ImageTest(TemplateTestCase):
    image_path = join(dirname(dirname(__file__)), 'assets', 'public', 'static', 'betty-512x512.png')

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
        async with self._render(template_string=template, data={
            'file': file,
        }) as (actual, site):
            self.assertEquals(expected, actual)
            for file_path in actual.split(':'):
                self.assertTrue(exists(join(site.configuration.www_directory_path, file_path[1:])))


class TestPlugin(Plugin):
    pass


class PluginsTest(TemplateTestCase):
    @sync
    async def test_with_unknown_plugin_module(self):
        template = '{% if "betty.UnknownModule.Plugin" in plugins %}true{% else %}false{% endif %}'
        async with self._render(template_string=template) as (actual, _):
            self.assertEquals('false', actual)

    @sync
    async def test_with_unknown_plugin_class(self):
        template = '{% if "betty.UnknownPlugin" in plugins %}true{% else %}false{% endif %}'
        async with self._render(template_string=template) as (actual, _):
            self.assertEquals('false', actual)

    @sync
    async def test_with_disabled_plugin(self):
        template = '{% if "' + TestPlugin.__module__ + '.TestPlugin" in plugins %}true{% else %}false{% endif %}'
        async with self._render(template_string=template) as (actual, _):
            self.assertEquals('false', actual)

    @sync
    async def test_with_enabled_plugin(self):
        template = '{% if "' + TestPlugin.__module__ + '.TestPlugin" in plugins %}true{% else %}false{% endif %}'

        def _update_configuration(configuration: Configuration) -> None:
            configuration.plugins[TestPlugin] = None
        async with self._render(template_string=template, update_configuration=_update_configuration) as (actual, _):
            self.assertEquals('true', actual)


class FormatDateTest(TemplateTestCase):
    @sync
    async def test(self):
        template = '{{ date | format_date }}'
        date = Date(1970, 1, 1)
        async with self._render(template_string=template, data={
            'date': date,
        }) as (actual, _):
            self.assertEquals('January 1, 1970', actual)


class SortLocalizedsTest(TemplateTestCase):
    class WithLocalizedNames:
        def __init__(self, identifier, names: List[PlaceName]):
            self.id = identifier
            self.names = names

        def __repr__(self):
            return self.id

    @sync
    async def test(self):
        template = '{{ data | sort_localizeds(localized_attribute="names", sort_attribute="name") }}'
        data = [
            self.WithLocalizedNames('third', [
                PlaceName('3', 'nl-NL'),
            ]),
            self.WithLocalizedNames('second', [
                PlaceName('2', 'en'),
                PlaceName('1', 'nl-NL'),
            ]),
            self.WithLocalizedNames('first', [
                PlaceName('2', 'nl-NL'),
                PlaceName('1', 'en-US'),
            ]),
        ]
        async with self._render(template_string=template, data={
            'data': data,
        }) as (actual, _):
            self.assertEquals('[first, second, third]', actual)

    @sync
    async def test_with_empty_iterable(self):
        template = '{{ data | sort_localizeds(localized_attribute="names", sort_attribute="name") }}'
        async with self._render(template_string=template, data={
            'data': [],
        }) as (actual, _):
            self.assertEquals('[]', actual)


class SelectLocalizedsTest(TemplateTestCase):
    @parameterized.expand([
        ('', 'en', []),
        ('Apple', 'en', [
            PlaceName('Apple', 'en')
        ]),
        ('Apple', 'en', [
            PlaceName('Apple', 'en-US')
        ]),
        ('Apple', 'en-US', [
            PlaceName('Apple', 'en')
        ]),
        ('', 'nl', [
            PlaceName('Apple', 'en')
        ]),
        ('', 'nl-NL', [
            PlaceName('Apple', 'en')
        ]),
    ])
    @sync
    async def test(self, expected: str, locale: str, data: Iterable[Localized]):
        template = '{{ data | select_localizeds | map(attribute="name") | join(", ") }}'

        def _update_configuration(configuration: Configuration) -> None:
            configuration.locales.clear()
            configuration.locales[locale] = LocaleConfiguration(locale)
        async with self._render(template_string=template, data={
            'data': data,
        }, update_configuration=_update_configuration) as (actual, _):
            self.assertEquals(expected, actual)


class SelectDatedsTest(TemplateTestCase):
    class DatedDummy(Dated):
        def __init__(self, value: str, date: Optional[Datey] = None):
            Dated.__init__(self)
            self._value = value
            self.date = date

        def __str__(self):
            return self._value

    @parameterized.expand([
        ('Apple', {
            'dateds': [
                DatedDummy('Apple'),
            ],
            'date': None,
        }),
        ('Apple', {
            'dateds': [
                DatedDummy('Apple'),
            ],
            'date': Date(),
        }),
        ('Apple', {
            'dateds': [
                DatedDummy('Apple'),
            ],
            'date': Date(1970, 1, 1),
        }),
        ('', {
            'dateds': [
                DatedDummy('Apple', Date(1970, 1, 1)),
            ],
            'date': None,
        }),
        ('', {
            'dateds': [
                DatedDummy('Apple', Date(1970, 1, 1)),
            ],
            'date': Date(),
        }),
        ('Apple', {
            'dateds': [
                DatedDummy('Apple', Date(1970, 1, 1)),
            ],
            'date': Date(1970, 1, 1),
        }),
        ('Apple, Strawberry', {
            'dateds': [
                DatedDummy('Apple', Date(1971, 1, 1)),
                DatedDummy('Strawberry', Date(1970, 1, 1)),
                DatedDummy('Banana', Date(1969, 1, 1)),
                DatedDummy('Orange', Date(1972, 12, 31)),
            ],
            'date': DateRange(Date(1970, 1, 1), Date(1971, 1, 1)),
        }),
    ])
    @sync
    async def test(self, expected: str, data: Dict):
        template = '{{ dateds | select_dateds(date=date) | join(", ") }}'
        async with self._render(template_string=template, data=data) as (actual, _):
            self.assertEquals(expected, actual)


class IsSubjectRoleTest(TemplateTestCase):
    @parameterized.expand([
        ('true', Subject()),
        ('false', Subject),
        ('false', Attendee()),
        ('false', 9),
    ])
    @sync
    async def test(self, expected, data) -> None:
        template = '{% if data is subject_role %}true{% else %}false{% endif %}'
        async with self._render(template_string=template, data={
            'data': data,
        }) as (actual, _):
            self.assertEquals(expected, actual)


class IsWitnessRoleTest(TemplateTestCase):
    @parameterized.expand([
        ('true', Witness()),
        ('false', Witness),
        ('false', Attendee()),
        ('false', 9),
    ])
    @sync
    async def test(self, expected, data) -> None:
        template = '{% if data is witness_role %}true{% else %}false{% endif %}'
        async with self._render(template_string=template, data={
            'data': data,
        }) as (actual, _):
            self.assertEquals(expected, actual)
