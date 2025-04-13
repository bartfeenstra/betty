from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import pytest
from typing_extensions import override

from betty.locale import (
    MULTIPLE_LOCALES,
    NO_LINGUISTIC_CONTENT,
    SPECIAL_LOCALES,
    LocaleSchema,
    Localey,
    merge_locales,
    negotiate_locale,
    to_locale,
)
from betty.test_utils.json.schema import SchemaTestBase

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.json.schema import Schema
    from betty.serde.dump import Dump


@pytest.mark.parametrize(
    ("expected", "locales"),
    [
        # No locales.
        (NO_LINGUISTIC_CONTENT, []),
        # A single locale which is passed through.
        ("nl", ["nl"]),
        ("de-DE", ["de-DE"]),
        *((locale, [locale]) for locale in SPECIAL_LOCALES),
        # Multiple locales.
        (MULTIPLE_LOCALES, ["nl", "de-DE"]),
        # Multiple locales, including no linguistic content.
        ("nl", ["nl", NO_LINGUISTIC_CONTENT]),
        (MULTIPLE_LOCALES, ["nl", "de-DE", NO_LINGUISTIC_CONTENT]),
        *(
            (locale, [locale, NO_LINGUISTIC_CONTENT])
            for locale in SPECIAL_LOCALES
            if locale is not NO_LINGUISTIC_CONTENT
        ),
    ],
)
def test_merge_locales(expected: str, locales: Sequence[str]) -> None:
    assert merge_locales(*locales) == expected


@pytest.mark.parametrize(
    ("expected", "preferred_locale", "available_locales"),
    [
        ("nl", "nl", ["nl"]),
        ("nl-NL", "nl", ["nl-NL"]),
        ("nl", "nl-NL", ["nl"]),
        ("nl-NL", "nl-NL", ["nl", "nl-BE", "nl-NL"]),
        ("nl", "nl", ["nl", "en"]),
        ("nl", "nl", ["en", "nl"]),
        ("nl-NL", "nl-BE", ["nl-NL"]),
    ],
)
async def test_negotiate_locale(
    expected: Localey | None,
    preferred_locale: Localey,
    available_locales: Sequence[Localey],
) -> None:
    actual = negotiate_locale(preferred_locale, available_locales)
    assert expected == (to_locale(actual) if actual else actual)


class TestLocaleSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                LocaleSchema(),
                ["en", "nl", "uk"],
                [
                    True,
                    False,
                ],
            )
        ]
