from __future__ import annotations

from pathlib import Path
from typing import Iterable, Any
from unittest.mock import Mock

import pytest
from typing_extensions import Self

from betty.app import App
from betty.jinja2 import Jinja2Renderer, _Citer, Jinja2Provider
from betty.locale import Date, Datey, DateRange, Localized
from betty.media_type import MediaType
from betty.model import get_entity_type_name, Entity
from betty.model.ancestry import File, PlaceName, Subject, Attendee, Witness, Dated, Person, Place, Citation
from betty.string import camel_case_to_snake_case
from betty.tempfile import TemporaryDirectory
from betty.tests import TemplateTestCase


class TestJinja2Provider:
    def test_globals(self) -> None:
        sut = Jinja2Provider()
        assert isinstance(sut.globals, dict)

    def test_filters(self) -> None:
        sut = Jinja2Provider()
        assert isinstance(sut.filters, dict)


class TestJinja2Renderer:
    async def test_render_file(self) -> None:
        with App() as app:
            sut = Jinja2Renderer(app.jinja2_environment, app.project.configuration)
            template = '{% if true %}true{% endif %}'
            expected_output = 'true'
            with TemporaryDirectory() as working_directory_path:
                template_file_path = working_directory_path / 'betty.txt.j2'
                with open(template_file_path, 'w') as f:
                    f.write(template)
                await sut.render_file(template_file_path)
                with open(Path(working_directory_path) / 'betty.txt') as f:
                    assert expected_output == f.read().strip()
                assert not template_file_path.exists()


class FilterFlattenTest(TemplateTestCase):
    @pytest.mark.parametrize('expected, template', [
        ('', '{{ [] | flatten | join(", ") }}'),
        ('', '{{ [[], [], []] | flatten | join(", ") }}'),
        ('kiwi, apple, banana',
         '{{ [["kiwi"], ["apple"], ["banana"]] | flatten | join(", ") }}'),
    ])
    def test(self, expected: str, template: str) -> None:
        with self._render(template_string=template) as (actual, _):
            assert expected == actual


class FilterWalkTest(TemplateTestCase):
    class WalkData:
        def __init__(self, label: str, children: Iterable[Self] | None = None):
            self._label = label
            self.children = children or []

        def __str__(self) -> str:
            return self._label

    @pytest.mark.parametrize('expected, template, data', [
        ('', '{{ data | walk("children") | join }}', WalkData('parent')),
        ('child1, child1child1, child2', '{{ data | walk("children") | join(", ") }}',
         WalkData('parent', [WalkData('child1', [WalkData('child1child1')]), WalkData('child2')])),
    ])
    def test(self, expected: str, template: str, data: WalkData) -> None:
        with self._render(template_string=template, data={
            'data': data,
        }) as (actual, _):
            assert expected == actual


class FilterParagraphsTest(TemplateTestCase):
    @pytest.mark.parametrize('expected, template', [
        ('<p></p>', '{{ "" | paragraphs }}'),
        ('<p>Apples <br>\n and <br>\n oranges</p>',
         '{{ "Apples \n and \n oranges" | paragraphs }}'),
    ])
    def test(self, expected: str, template: str) -> None:
        with self._render(template_string=template) as (actual, _):
            assert expected == actual


class FilterFormatDegreesTest(TemplateTestCase):
    @pytest.mark.parametrize('expected, template', [
        ('0° 0&#39; 0&#34;', '{{ 0 | format_degrees }}'),
        ('52° 22&#39; 1&#34;', '{{ 52.367 | format_degrees }}'),
    ])
    def test(self, expected: str, template: str) -> None:
        with self._render(template_string=template) as (actual, _):
            assert expected == actual


class FilterUniqueTest(TemplateTestCase):
    def test(self) -> None:
        data: list[Any] = [
            999,
            {},
            999,
            {},
        ]
        with self._render(template_string='{{ data | unique | join(", ") }}', data={
            'data': data,
        }) as (actual, _):
            assert '999 == {}', actual


class FilterMapTest(TemplateTestCase):
    class MapData:
        def __init__(self, label):
            self.label = label

    @pytest.mark.parametrize('expected, template, data', [
        ('kiwi, apple, banana', '{{ data | map(attribute="label") | join(", ") }}',
         [MapData('kiwi'), MapData('apple'), MapData('banana')]),
        ('kiwi, None, apple, None, banana',
         '{% macro print_string(value) %}{% if value is none %}None{% else %}{{ value }}{% endif %}{% endmacro %}{{ ["kiwi", None, "apple", None, "banana"] | map(print_string) | join(", ") }}',
         {}),
    ])
    def test(self, expected: str, template: str, data: MapData) -> None:
        with self._render(template_string=template, data={
            'data': data,
        }) as (actual, _):
            assert expected == actual


class FilterFileTest(TemplateTestCase):
    @pytest.mark.parametrize('expected, template, file', [
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
    def test(self, expected: str, template: str, file: File) -> None:
        with self._render(template_string=template, data={
            'file': file,
        }) as (actual, app):
            assert expected == actual
            for file_path in actual.split(':'):
                assert ((app.project.configuration.www_directory_path / file_path[1:]).exists())


class FilterImageTest(TemplateTestCase):
    image_path = Path(__file__).parents[1] / 'assets' / 'public' / 'static' / 'betty-512x512.png'

    @pytest.mark.parametrize('expected, template, file', [
        ('/file/F1-99x-.png',
         '{{ file | image(width=99) }}', File('F1', image_path, media_type=MediaType('image/png'))),
        ('/file/F1--x99.png',
         '{{ file | image(height=99) }}', File('F1', image_path, media_type=MediaType('image/png'))),
        ('/file/F1-99x99.png',
         '{{ file | image(width=99, height=99) }}', File('F1', image_path, media_type=MediaType('image/png'))),
        ('/file/F1-99x99.png:/file/F1-99x99.png',
         '{{ file | image(width=99, height=99) }}:{{ file | image(width=99, height=99) }}', File('F1', image_path, media_type=MediaType('image/png'))),
    ])
    def test(self, expected: str, template: str, file: File) -> None:
        with self._render(template_string=template, data={
            'file': file,
        }) as (actual, app):
            assert expected == actual
            for file_path in actual.split(':'):
                assert ((app.project.configuration.www_directory_path / file_path[1:]).exists())

    def test_without_width(self) -> None:
        file = File('F1', self.image_path, media_type=MediaType('image/png'))
        with pytest.raises(ValueError):
            with self._render(template_string='{{ file | image }}', data={
                'file': file,
            }):
                pass


class GlobalCiterTest(TemplateTestCase):
    def test_cite(self) -> None:
        citation1 = Mock(Citation)
        citation2 = Mock(Citation)
        sut = _Citer()
        assert 1 == sut.cite(citation1)
        assert 2 == sut.cite(citation2)
        assert 1 == sut.cite(citation1)

    def test_iter(self) -> None:
        citation1 = Mock(Citation)
        citation2 = Mock(Citation)
        sut = _Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        assert [(1, citation1), (2, citation2)] == list(sut)

    def test_len(self) -> None:
        citation1 = Mock(Citation)
        citation2 = Mock(Citation)
        sut = _Citer()
        sut.cite(citation1)
        sut.cite(citation2)
        assert 2 == len(sut)


class FormatDateyTest(TemplateTestCase):
    def test(self) -> None:
        template = '{{ date | format_datey }}'
        date = Date(1970, 1, 1)
        with self._render(template_string=template, data={
            'date': date,
        }) as (actual, _):
            assert 'January 1 == 1970', actual


class FilterSortLocalizedsTest(TemplateTestCase):
    class WithLocalizedNames:
        def __init__(self, identifier: str, names: list[PlaceName]):
            self.id = identifier
            self.names = names

        def __repr__(self) -> str:
            return self.id

    def test(self) -> None:
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
        with self._render(template_string=template, data={
            'data': data,
        }) as (actual, _):
            assert '[first == second, third]', actual

    def test_with_empty_iterable(self) -> None:
        template = '{{ data | sort_localizeds(localized_attribute="names", sort_attribute="name") }}'
        with self._render(template_string=template, data={
            'data': [],
        }) as (actual, _):
            assert '[]' == actual


class FilterSelectLocalizedsTest(TemplateTestCase):
    @pytest.mark.parametrize('expected, locale, data', [
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
    def test(self, expected: str, locale: str, data: Iterable[Localized]) -> None:
        template = '{{ data | select_localizeds | map(attribute="name") | join(", ") }}'

        with self._render(template_string=template, data={
            'data': data,
        }, locale=locale) as (actual, _):
            assert expected == actual

    def test_include_unspecified(self) -> None:
        template = '{{ data | select_localizeds(include_unspecified=true) | map(attribute="name") | join(", ") }}'
        data = [
            PlaceName('Apple', 'zxx'),
            PlaceName('Apple', 'und'),
            PlaceName('Apple', 'mul'),
            PlaceName('Apple', 'mis'),
            PlaceName('Apple', None),
        ]

        with self._render(template_string=template, data={
            'data': data,
        }, locale='en-US') as (actual, _):
            assert 'Apple == Apple, Apple, Apple, Apple', actual


class FilterSelectDatedsTest(TemplateTestCase):
    class DatedDummy(Dated):
        def __init__(self, value: str, date: Datey | None = None):
            Dated.__init__(self)
            self._value = value
            self.date = date

        def __str__(self) -> str:
            return self._value

    @pytest.mark.parametrize('expected, data', [
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
    def test(self, expected: str, data: dict[str, Any]) -> None:
        template = '{{ dateds | select_dateds(date=date) | join(", ") }}'
        with self._render(template_string=template, data=data) as (actual, _):
            assert expected == actual


class TestSubjectRoleTest(TemplateTestCase):
    @pytest.mark.parametrize('expected, data', [
        ('true', Subject()),
        ('false', Subject),
        ('false', Attendee()),
        ('false', 9),
    ])
    def test(self, expected: str, data: dict[str, Any]) -> None:
        template = '{% if data is subject_role %}true{% else %}false{% endif %}'
        with self._render(template_string=template, data={
            'data': data,
        }) as (actual, _):
            assert expected == actual


class TestWitnessRoleTest(TemplateTestCase):
    @pytest.mark.parametrize('expected, data', [
        ('true', Witness()),
        ('false', Witness),
        ('false', Attendee()),
        ('false', 9),
    ])
    def test(self, expected: str, data: dict[str, Any]) -> None:
        template = '{% if data is witness_role %}true{% else %}false{% endif %}'
        with self._render(template_string=template, data={
            'data': data,
        }) as (actual, _):
            assert expected == actual


class TestResourceTest(TemplateTestCase):
    @pytest.mark.parametrize('expected, entity_type, data', [
        ('true', Person, Person('P1')),
        ('false', Person, Place('P1', [PlaceName('The Place')])),
        ('true', Place, Place('P1', [PlaceName('The Place')])),
        ('false', Place, Person('P1')),
        ('false', Place, 999),
        ('false', Person, object()),
    ])
    def test(self, expected: str, entity_type: type[Entity], data: dict[str, Any]) -> None:
        template = f'{{% if data is {camel_case_to_snake_case(get_entity_type_name(entity_type))}_entity %}}true{{% else %}}false{{% endif %}}'
        with self._render(template_string=template, data={
            'data': data,
        }) as (actual, _):
            assert expected == actual
