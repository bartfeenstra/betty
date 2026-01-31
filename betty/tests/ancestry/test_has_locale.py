from __future__ import annotations

from typing import TYPE_CHECKING, Any

from babel import Locale

from betty.ancestry.has_locale import HasLocale
from betty.locale import resolve_locale
from betty.test_utils.json.linked_data import assert_dumps_linked_data

if TYPE_CHECKING:
    from collections.abc import Mapping


class TestHasLocale:
    def test_locale_without___init___locale(self) -> None:
        sut = HasLocale()
        assert sut.locale is None

    def test_locale_with___init___locale(self) -> None:
        locale = Locale("nl")
        sut = HasLocale(locale=locale)
        assert sut.locale is locale

    def test_locale(self) -> None:
        locale = Locale("nl")
        sut = HasLocale()
        sut.locale = locale
        assert sut.locale == locale

    async def test_dump_linked_data__without_locale(self) -> None:
        sut = HasLocale()
        expected = {"locale": "und"}
        actual = await assert_dumps_linked_data(sut)
        assert actual == expected

    async def test_dump_linked_data__with_locale(self) -> None:
        locale = "en-US"
        sut = HasLocale(locale=resolve_locale(locale))
        expected: Mapping[str, Any] = {
            "locale": locale,
        }
        actual = await assert_dumps_linked_data(sut)
        assert actual == expected
