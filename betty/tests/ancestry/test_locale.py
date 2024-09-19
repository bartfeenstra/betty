from __future__ import annotations

from typing import Mapping, Any

from betty.locale import UNDETERMINED_LOCALE
from betty.test_utils.ancestry.locale import DummyHasLocale
from betty.test_utils.json.linked_data import assert_dumps_linked_data


class TestHasLocale:
    def test_locale_without___init___locale(self) -> None:
        sut = DummyHasLocale()
        assert sut.locale == UNDETERMINED_LOCALE

    def test_locale_with___init___locale(self) -> None:
        locale = "nl"
        sut = DummyHasLocale(locale=locale)
        assert sut.locale == locale

    def test_locale(self) -> None:
        locale = "nl"
        sut = DummyHasLocale()
        sut.locale = locale
        assert sut.locale == locale

    async def test_dump_linked_data(self) -> None:
        sut = DummyHasLocale()
        expected: Mapping[str, Any] = {
            "locale": UNDETERMINED_LOCALE,
        }
        actual = await assert_dumps_linked_data(sut)
        assert actual == expected
