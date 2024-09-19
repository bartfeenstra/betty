from __future__ import annotations

from typing import Any, TYPE_CHECKING

import pytest

from betty.ancestry.name import Name
from betty.ancestry.place import Place
from betty.date import DateRange, Date
from betty.extension.cotton_candy import CottonCandy
from betty.test_utils.assets.templates import TemplateTestBase

if TYPE_CHECKING:
    from collections.abc import MutableMapping


class Test(TemplateTestBase):
    extensions = {CottonCandy}
    template_file = "entity/label--place.html.j2"

    @pytest.mark.parametrize(
        ("expected", "data", "locale"),
        [
            (
                '<span><a href="/place/P0/index.html"><span lang="und">The Place</span></a></span>',
                {
                    "entity": Place(
                        id="P0",
                        names=[Name("The Place")],
                    ),
                },
                None,
            ),
            (
                '<span><a href="/place/P0/index.html"><span lang="en">The Place</span></a></span>',
                {
                    "entity": Place(
                        id="P0",
                        names=[Name({"en": "The Place"})],
                    ),
                },
                None,
            ),
            (
                '<span><a href="/place/P0/index.html">De Plaats</a></span>',
                {
                    "entity": Place(
                        id="P0",
                        names=[
                            Name({"en": "The Place", "nl": "De Plaats"}),
                        ],
                    ),
                },
                "nl",
            ),
            (
                '<span><span lang="und">The Place</span></span>',
                {
                    "entity": Place(
                        id="P0",
                        names=[Name("The Place")],
                    ),
                    "embedded": True,
                },
                None,
            ),
            (
                '<span><a href="/place/P0/index.html">De Nieuwe Plaats</a></span>',
                {
                    "entity": Place(
                        id="P0",
                        names=[
                            Name(
                                {"en": "The Old Place"},
                                date=DateRange(None, Date(1969, 12, 31)),
                            ),
                            Name(
                                {"nl": "De Nieuwe Plaats"},
                                date=DateRange(Date(1970, 1, 1)),
                            ),
                        ],
                    ),
                    "date_context": Date(1970, 1, 1),
                },
                "nl",
            ),
        ],
    )
    async def test(
        self, expected: str, data: MutableMapping[str, Any], locale: str | None
    ) -> None:
        async with self._render(data=data, locale=locale) as (actual, _):
            assert actual == expected
