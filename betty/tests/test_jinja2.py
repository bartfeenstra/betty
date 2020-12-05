from os import makedirs, path
from tempfile import TemporaryDirectory
from typing import List, Dict, Optional, Iterable, Type
from unittest import TestCase
from unittest.mock import Mock

from parameterized import parameterized

from betty.ancestry import File, PlaceName, Subject, Attendee, Witness, Dated, Resource, Person, Place, Citation
from betty.config import Configuration, LocaleConfiguration
from betty.asyncio import sync
from betty.jinja2 import Jinja2Renderer, _Citer, Jinja2Provider
from betty.locale import Date, Datey, DateRange, Localized
from betty.media_type import MediaType
from betty.plugin import Plugin
from betty.site import Site
from betty.tests import TemplateTestCase


class Jinja2ProviderTest(TestCase):
    def test_globals(self) -> None:
        sut = Jinja2Provider()
        self.assertIsInstance(sut.globals, dict)

    def test_filters(self) -> None:
        sut = Jinja2Provider()
        self.assertIsInstance(sut.filters, dict)


class Jinja2RendererTest(TestCase):
    @sync
    async def test_render_file(self) -> None:
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://ancestry.example.com')
            async with Site(configuration) as site:
                sut = Jinja2Renderer(site.jinja2_environment, configuration)
                template = '{% if true %}true{% endif %}'
                expected_output = 'true'
                with TemporaryDirectory() as working_directory_path:
                    template_file_path = path.join(working_directory_path, 'betty.txt.j2')
                    with open(template_file_path, 'w') as f:
                        f.write(template)
                    await sut.render_file(template_file_path)
                    with open(path.join(working_directory_path, 'betty.txt')) as f:
                        self.assertEquals(expected_output, f.read().strip())
                    self.assertFalse(path.exists(template_file_path))

    @sync
    async def test_render_file_should_ignore_non_sass_or_scss(self) -> None:
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://ancestry.example.com')
            async with Site(configuration) as site:
                sut = Jinja2Renderer(site.jinja2_environment, configuration)
                template = '{% if true %}true{% endif %}'
                with TemporaryDirectory() as working_directory_path:
                    template_file_path = path.join(working_directory_path, 'betty.txt')
                    with open(template_file_path, 'w') as f:
                        f.write(template)
                    await sut.render_file(template_file_path)
                    with open(path.join(working_directory_path, 'betty.txt')) as f:
                        self.assertEquals(template, f.read())

    @sync
    async def test_render_tree(self) -> None:
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(output_directory_path, 'https://ancestry.example.com')
            async with Site(configuration) as site:
                sut = Jinja2Renderer(site.jinja2_environment, configuration)
                template = '{% if true %}true{% endif %}'
                expected_output = 'true'
                with TemporaryDirectory() as working_directory_path:
                    working_subdirectory_path = path.join(working_directory_path, 'sub')
                    makedirs(working_subdirectory_path)
                    scss_file_path = path.join(working_subdirectory_path, 'betty.txt.j2')
                    with open(scss_file_path, 'w') as f:
                        f.write(template)
                    await sut.render_tree(working_directory_path)
                    with open(path.join(working_subdirectory_path, 'betty.txt')) as f:
                        self.assertEquals(expected_output, f.read().strip())
                    self.assertFalse(path.exists(scss_file_path))


class FilterFlattenTest(TemplateTestCase):
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


class FilterWalkTest(TemplateTestCase):
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


class FilterParagraphsTest(TemplateTestCase):
    @parameterized.expand([
        ('<p></p>', '{{ "" | paragraphs }}'),
        ('<p>Apples <br>\n and <br>\n oranges</p>',
         '{{ "Apples \n and \n oranges" | paragraphs }}'),
    ])
    @sync
    async def test(self, expected, template):
        async with self._render(template_string=template) as (actual, _):
            self.assertEquals(expected, actual)


class FilterFormatDegreesTest(TemplateTestCase):
    @parameterized.expand([
        ('0° 0&#39; 0&#34;', '{{ 0 | format_degrees }}'),
        ('52° 22&#39; 1&#34;', '{{ 52.367 | format_degrees }}'),
    ])
    @sync
    async def test(self, expected, template):
        async with self._render(template_string=template) as (actual, _):
            self.assertEquals(expected, actual)


class FilterUniqueTest(TemplateTestCase):
    @sync
    async def test(self):
        data = [
            999,
            {},
            999,
            {},
        ]
        async with self._render(template_string='{{ data | unique | join(", ") }}', data={
            'data': data,
        }) as (actual, _):
            self.assertEquals('999, {}', actual)


class FilterMapTest(TemplateTestCase):
    class MapData:
        def __init__(self, label):
            self.label = label

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


class FilterFileTest(TemplateTestCase):
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
                self.assertTrue(path.exists(path.join(site.configuration.www_directory_path, file_path[1:])))


class FilterImageTest(TemplateTestCase):
    image_path = path.join(path.dirname(path.dirname(__file__)), 'assets', 'public', 'static', 'betty-512x512.png')

    @parameterized.expand([
        ('/file/F1-99x-.png',
         '{{ file | image(width=99) }}', File('F1', image_path, media_type=MediaType('image/png'))),
        ('/file/F1--x99.png',
         '{{ file | image(height=99) }}', File('F1', image_path, media_type=MediaType('image/png'))),
        ('/file/F1-99x99.png',
         '{{ file | image(width=99, height=99) }}', File('F1', image_path, media_type=MediaType('image/png'))),
        ('/file/F1-99x99.png:/file/F1-99x99.png',
         '{{ file | image(width=99, height=99) }}:{{ file | image(width=99, height=99) }}', File('F1', image_path, media_type=MediaType('image/png'))),
    ])
    @sync
    async def test(self, expected, template, file):
        async with self._render(template_string=template, data={
            'file': file,
        }) as (actual, site):
            self.assertEquals(expected, actual)
            for file_path in actual.split(':'):
                self.assertTrue(path.exists(path.join(site.configuration.www_directory_path, file_path[1:])))

    @sync
    async def test_without_width(self):
        file = File('F1', self.image_path, media_type=MediaType('image/png'))
        with self.assertRaises(ValueError):
            async with self._render(template_string='{{ file | image }}', data={
                'file': file,
            }):
                pass


class TestPlugin(Plugin):
    """
    This class must be top-level. Otherwise it cannot be imported by its fully qualified name.
    """
    pass


class GlobalPluginsTest(TemplateTestCase):
    @sync
    async def test_getitem_with_unknown_plugin(self):
        template = '{{ plugins["betty.UnknownPlugin"] | default("false") }}'
        async with self._render(template_string=template) as (actual, _):
            self.assertEquals('false', actual)

    @sync
    async def test_getitem_with_disabled_plugin(self):
        template = '{{ plugins["%s"] | default("false") }}' % TestPlugin.name()
        async with self._render(template_string=template) as (actual, _):
            self.assertEquals('false', actual)

    @sync
    async def test_getitem_with_enabled_plugin(self):
        template = '{%% if plugins["%s"] is not none %%}true{%% else %%}false{%% endif %%}' % TestPlugin.name()

        def _update_configuration(configuration: Configuration) -> None:
            configuration.plugins[TestPlugin] = None
        async with self._render(template_string=template, update_configuration=_update_configuration) as (actual, _):
            self.assertEquals('true', actual)

    @sync
    async def test_contains_with_unknown_plugin(self):
        template = '{% if "betty.UnknownPlugin" in plugins %}true{% else %}false{% endif %}'
        async with self._render(template_string=template) as (actual, _):
            self.assertEquals('false', actual)

    @sync
    async def test_contains_with_disabled_plugin(self):
        template = '{%% if "%s" in plugins %%}true{%% else %%}false{%% endif %%}' % TestPlugin.name()
        async with self._render(template_string=template) as (actual, _):
            self.assertEquals('false', actual)

    @sync
    async def test_contains_with_enabled_plugin(self):
        template = '{%% if "%s" in plugins %%}true{%% else %%}false{%% endif %%}' % TestPlugin.name()

        def _update_configuration(configuration: Configuration) -> None:
            configuration.plugins[TestPlugin] = None
        async with self._render(template_string=template, update_configuration=_update_configuration) as (actual, _):
            self.assertEquals('true', actual)


class GlobalCiterTest(TemplateTestCase):
    @sync
    async def test_cite(self):
        citation1 = Mock(Citation)
        citation2 = Mock(Citation)
        sut = _Citer()
        self.assertEquals(1, sut.cite(citation1))
        self.assertEquals(2, sut.cite(citation2))
        self.assertEquals(1, sut.cite(citation1))

    @sync
    async def test_iter(self):
        citation1 = Mock(Citation)
        citation2 = Mock(Citation)
        sut = _Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        self.assertEquals([(1, citation1), (2, citation2)], list(sut))

    @sync
    async def test_len(self):
        citation1 = Mock(Citation)
        citation2 = Mock(Citation)
        sut = _Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        self.assertEquals(2, len(sut))


class FormatDateTest(TemplateTestCase):
    @sync
    async def test(self):
        template = '{{ date | format_date }}'
        date = Date(1970, 1, 1)
        async with self._render(template_string=template, data={
            'date': date,
        }) as (actual, _):
            self.assertEquals('January 1, 1970', actual)


class FilterSortLocalizedsTest(TemplateTestCase):
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


class FilterSelectLocalizedsTest(TemplateTestCase):
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

    @sync
    async def test_include_unspecified(self):
        template = '{{ data | select_localizeds(include_unspecified=true) | map(attribute="name") | join(", ") }}'
        data = [
            PlaceName('Apple', 'zxx'),
            PlaceName('Apple', 'und'),
            PlaceName('Apple', 'mul'),
            PlaceName('Apple', 'mis'),
            PlaceName('Apple', None),
        ]

        def _update_configuration(configuration: Configuration) -> None:
            configuration.locales.clear()
            configuration.locales['en-US'] = LocaleConfiguration('en-US')
        async with self._render(template_string=template, data={
            'data': data,
        }, update_configuration=_update_configuration) as (actual, _):
            self.assertEquals('Apple, Apple, Apple, Apple, Apple', actual)


class FilterSelectDatedsTest(TemplateTestCase):
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


class TestSubjectRoleTest(TemplateTestCase):
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


class TestWitnessRoleTest(TemplateTestCase):
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


class TestResourceTest(TemplateTestCase):
    @parameterized.expand([
        ('true', Person, Person('P1')),
        ('false', Person, Place('P1', [PlaceName('The Place')])),
        ('true', Place, Place('P1', [PlaceName('The Place')])),
        ('false', Place, Person('P1')),
        ('false', Place, 999),
        ('false', Person, object()),
    ])
    @sync
    async def test(self, expected, resource_type: Type[Resource], data) -> None:
        template = f'{{% if data is {resource_type.resource_type_name()}_resource %}}true{{% else %}}false{{% endif %}}'
        async with self._render(template_string=template, data={
            'data': data,
        }) as (actual, _):
            self.assertEquals(expected, actual)
