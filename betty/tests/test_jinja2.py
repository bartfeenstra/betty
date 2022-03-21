from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Dict, Optional, Iterable, Type
from unittest.mock import Mock

from parameterized import parameterized

from betty.app import App, Configuration, LocaleConfiguration
from betty.asyncio import sync
from betty.jinja2 import Jinja2Renderer, _Citer, Jinja2Provider
from betty.locale import Date, Datey, DateRange, Localized
from betty.media_type import MediaType
from betty.model import get_entity_type_name
from betty.model.ancestry import File, PlaceName, Subject, Attendee, Witness, Dated, Entity, Person, Place, Citation
from betty.string import camel_case_to_snake_case
from betty.tests import TemplateTestCase, TestCase


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
        async with App() as app:
            sut = Jinja2Renderer(app.jinja2_environment, app.configuration)
            template = '{% if true %}true{% endif %}'
            expected_output = 'true'
            with TemporaryDirectory() as working_directory_path:
                template_file_path = Path(working_directory_path) / 'betty.txt.j2'
                with open(template_file_path, 'w') as f:
                    f.write(template)
                await sut.render_file(template_file_path)
                with open(Path(working_directory_path) / 'betty.txt') as f:
                    self.assertEqual(expected_output, f.read().strip())
                self.assertFalse(template_file_path.exists())

    @sync
    async def test_render_tree(self) -> None:
        async with App() as app:
            sut = Jinja2Renderer(app.jinja2_environment, app.configuration)
            template = '{% if true %}true{% endif %}'
            expected_output = 'true'
            with TemporaryDirectory() as working_directory_path:
                working_subdirectory_path = Path(working_directory_path) / 'sub'
                working_subdirectory_path.mkdir(parents=True)
                scss_file_path = Path(working_subdirectory_path) / 'betty.txt.j2'
                with open(scss_file_path, 'w') as f:
                    f.write(template)
                await sut.render_tree(working_directory_path)
                with open(Path(working_subdirectory_path) / 'betty.txt') as f:
                    self.assertEqual(expected_output, f.read().strip())
                self.assertFalse(scss_file_path.exists())


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
            self.assertEqual(expected, actual)


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
            self.assertEqual(expected, actual)


class FilterParagraphsTest(TemplateTestCase):
    @parameterized.expand([
        ('<p></p>', '{{ "" | paragraphs }}'),
        ('<p>Apples <br>\n and <br>\n oranges</p>',
         '{{ "Apples \n and \n oranges" | paragraphs }}'),
    ])
    @sync
    async def test(self, expected, template):
        async with self._render(template_string=template) as (actual, _):
            self.assertEqual(expected, actual)


class FilterFormatDegreesTest(TemplateTestCase):
    @parameterized.expand([
        ('0° 0&#39; 0&#34;', '{{ 0 | format_degrees }}'),
        ('52° 22&#39; 1&#34;', '{{ 52.367 | format_degrees }}'),
    ])
    @sync
    async def test(self, expected, template):
        async with self._render(template_string=template) as (actual, _):
            self.assertEqual(expected, actual)


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
            self.assertEqual('999, {}', actual)


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
            self.assertEqual(expected, actual)


class FilterFileTest(TemplateTestCase):
    @parameterized.expand([
        (
            '/file/F1/file/test_jinja2.py',
            '{{ file | file }}',
            File('F1', Path(__file__)),
        ),
        (
            '/file/F1/file/test_jinja2.py:/file/F1/file/test_jinja2.py',
            '{{ file | file }}:{{ file | file }}',
            File('F1', Path(__file__)),
        ),
    ])
    @sync
    async def test(self, expected, template, file):
        async with self._render(template_string=template, data={
            'file': file,
        }) as (actual, app):
            self.assertEqual(expected, actual)
            for file_path in actual.split(':'):
                self.assertTrue((app.configuration.www_directory_path / file_path[1:]).exists())


class FilterImageTest(TemplateTestCase):
    image_path = Path(__file__).parents[1] / 'assets' / 'public' / 'static' / 'betty-512x512.png'

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
        }) as (actual, app):
            self.assertEqual(expected, actual)
            for file_path in actual.split(':'):
                self.assertTrue((app.configuration.www_directory_path / file_path[1:]).exists())

    @sync
    async def test_without_width(self):
        file = File('F1', self.image_path, media_type=MediaType('image/png'))
        with self.assertRaises(ValueError):
            async with self._render(template_string='{{ file | image }}', data={
                'file': file,
            }):
                pass


class GlobalCiterTest(TemplateTestCase):
    @sync
    async def test_cite(self):
        citation1 = Mock(Citation)
        citation2 = Mock(Citation)
        sut = _Citer()
        self.assertEqual(1, sut.cite(citation1))
        self.assertEqual(2, sut.cite(citation2))
        self.assertEqual(1, sut.cite(citation1))

    @sync
    async def test_iter(self):
        citation1 = Mock(Citation)
        citation2 = Mock(Citation)
        sut = _Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        self.assertEqual([(1, citation1), (2, citation2)], list(sut))

    @sync
    async def test_len(self):
        citation1 = Mock(Citation)
        citation2 = Mock(Citation)
        sut = _Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        self.assertEqual(2, len(sut))


class FormatDateTest(TemplateTestCase):
    @sync
    async def test(self):
        template = '{{ date | format_date }}'
        date = Date(1970, 1, 1)
        async with self._render(template_string=template, data={
            'date': date,
        }) as (actual, _):
            self.assertEqual('January 1, 1970', actual)


class FilterSortLocalizedsTest(TemplateTestCase):
    class WithLocalizedNames:
        def __init__(self, identifier, names: List[PlaceName]):
            self.id = identifier
            self.names = names

        def __repr__(self) -> str:
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
            self.assertEqual('[first, second, third]', actual)

    @sync
    async def test_with_empty_iterable(self):
        template = '{{ data | sort_localizeds(localized_attribute="names", sort_attribute="name") }}'
        async with self._render(template_string=template, data={
            'data': [],
        }) as (actual, _):
            self.assertEqual('[]', actual)


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
            configuration.locales.replace([LocaleConfiguration(locale)])
        async with self._render(template_string=template, data={
            'data': data,
        }, update_configuration=_update_configuration) as (actual, _):
            self.assertEqual(expected, actual)

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
            configuration.locales.replace([LocaleConfiguration('en-US')])
        async with self._render(template_string=template, data={
            'data': data,
        }, update_configuration=_update_configuration) as (actual, _):
            self.assertEqual('Apple, Apple, Apple, Apple, Apple', actual)


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
            self.assertEqual(expected, actual)


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
            self.assertEqual(expected, actual)


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
            self.assertEqual(expected, actual)


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
    async def test(self, expected, entity_type: Type[Entity], data) -> None:
        template = f'{{% if data is {camel_case_to_snake_case(get_entity_type_name(entity_type))}_entity %}}true{{% else %}}false{{% endif %}}'
        async with self._render(template_string=template, data={
            'data': data,
        }) as (actual, _):
            self.assertEqual(expected, actual)
