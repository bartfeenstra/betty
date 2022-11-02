from typing import Optional, ContextManager

import pytest

from betty.app import App
from betty.cotton_candy import CottonCandy
from betty.locale import DateRange, Date
from betty.model.ancestry import Place, PlaceName
from betty.tests import TemplateTestCase


class Test(TemplateTestCase):
    extensions = {CottonCandy}
    template_file = 'entity/label--place.html.j2'

    @pytest.mark.parametrize('expected, data, locale', [
        (
            '<address><a href="/place/P0/index.html"><span>The Place</span></a></address>',
            {
                'entity': Place('P0', [PlaceName('The Place')]),
            },
            None,
        ),
        (
            '<address><a href="/place/P0/index.html"><span lang="en">The Place</span></a></address>',
            {
                'entity': Place('P0', [PlaceName('The Place', 'en')]),
            },
            None,
        ),
        (
            '<address><a href="/place/P0/index.html"><span lang="nl">De Plaats</span></a></address>',
            {
                'entity': Place('P0', [PlaceName('The Place', 'en'), PlaceName('De Plaats', 'nl')]),
            },
            'nl',
        ),
        (
            '<address><span>The Place</span></address>',
            {
                'entity': Place('P0', [PlaceName('The Place')]),
                'embedded': True,
            },
            None,
        ),
        (
            '<address><a href="/place/P0/index.html"><span lang="nl">De Nieuwe Plaats</span></a></address>',
            {
                'entity': Place('P0', [
                    PlaceName('The Old Place', 'en', date=DateRange(None, Date(1969, 12, 31))),
                    PlaceName('De Nieuwe Plaats', 'nl', date=DateRange(Date(1970, 1, 1))),
                ]),
                'date_context': Date(1970, 1, 1),
            },
            'nl',
        ),
    ])
    def test(self, expected: str, data, locale: Optional[str]) -> None:
        def _set_up(app: App) -> ContextManager[None]:
            return app.acquire_locale(locale)  # type: ignore

        with self._render(data=data, set_up=_set_up) as (actual, _):
            assert expected == actual
