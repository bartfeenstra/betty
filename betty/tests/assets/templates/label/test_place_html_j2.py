from typing import Optional

from parameterized import parameterized

from betty.locale import DateRange, Date
from betty.model.ancestry import Place, PlaceName
from betty.project import Configuration, LocaleConfiguration
from betty.tests import TemplateTestCase


class Test(TemplateTestCase):
    template_file = 'label/place.html.j2'

    @parameterized.expand([
        (
            '<address><a href="/place/P0/index.html"><span>The Place</span></a></address>',
            {
                'place': Place('P0', [PlaceName('The Place')]),
            },
        ),
        (
            '<address><a href="/place/P0/index.html"><span lang="en">The Place</span></a></address>',
            {
                'place': Place('P0', [PlaceName('The Place', 'en')]),
            },
        ),
        (
            '<address><a href="/place/P0/index.html"><span lang="nl">De Plaats</span></a></address>',
            {
                'place': Place('P0', [PlaceName('The Place', 'en'), PlaceName('De Plaats', 'nl')]),
            },
            'nl',
        ),
        (
            '<address><span>The Place</span></address>',
            {
                'place': Place('P0', [PlaceName('The Place')]),
                'embedded': True,
            },
        ),
        (
            '<address><a href="/place/P0/index.html"><span lang="nl">De Nieuwe Plaats</span></a></address>',
            {
                'place': Place('P0', [
                    PlaceName('The Old Place', 'en', date=DateRange(None, Date(1969, 12, 31))),
                    PlaceName('De Nieuwe Plaats', 'nl', date=DateRange(Date(1970, 1, 1))),
                ]),
                'date_context': Date(1970, 1, 1),
            },
            'nl',
        ),
    ])
    def test(self, expected, data, locale: Optional[str] = None) -> None:
        def _update_configuration(configuration: Configuration) -> None:
            if locale:
                configuration.locales.replace([LocaleConfiguration(locale)])

        with self._render(data=data, update_project_configuration=_update_configuration) as (actual, _):
            self.assertEqual(expected, actual)
