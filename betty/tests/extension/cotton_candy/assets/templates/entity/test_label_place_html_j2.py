from __future__ import annotations

from typing import Any, TYPE_CHECKING

import pytest

from betty.ancestry import Place, PlaceName
from betty.extension.cotton_candy import CottonCandy
from betty.locale.date import DateRange, Date
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
                '<span><a href="/place/P0/index.html"><span>The Place</span></a></span>',
                {
                    "entity": Place(
                        id="P0",
                        names=[PlaceName(name="The Place")],
                    ),
                },
                None,
            ),
            (
                '<span><a href="/place/P0/index.html"><span lang="en">The Place</span></a></span>',
                {
                    "entity": Place(
                        id="P0",
                        names=[
                            PlaceName(
                                name="The Place",
                                locale="en",
                            )
                        ],
                    ),
                },
                None,
            ),
            (
                '<span><a href="/place/P0/index.html"><span lang="nl">De Plaats</span></a></span>',
                {
                    "entity": Place(
                        id="P0",
                        names=[
                            PlaceName(
                                name="The Place",
                                locale="en",
                            ),
                            PlaceName(
                                name="De Plaats",
                                locale="nl",
                            ),
                        ],
                    ),
                },
                "nl",
            ),
            (
                "<span><span>The Place</span></span>",
                {
                    "entity": Place(
                        id="P0",
                        names=[PlaceName(name="The Place")],
                    ),
                    "embedded": True,
                },
                None,
            ),
            (
                '<span><a href="/place/P0/index.html"><span lang="nl">De Nieuwe Plaats</span></a></span>',
                {
                    "entity": Place(
                        id="P0",
                        names=[
                            PlaceName(
                                name="The Old Place",
                                locale="en",
                                date=DateRange(None, Date(1969, 12, 31)),
                            ),
                            PlaceName(
                                name="De Nieuwe Plaats",
                                locale="nl",
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
            assert expected == actual
