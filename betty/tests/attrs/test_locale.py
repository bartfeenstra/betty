from __future__ import annotations

from typing import TYPE_CHECKING, Any

from babel import Locale

from betty.attrs.locale import HasLocale, new_locale_attr
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG, resolve_locale
from betty.prop import HasProps

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.test_utils.conftest import AssertDumpsLinkedData


class _Owner(HasProps):
    locale = new_locale_attr()


def test_new_locale_attr__set() -> None:
    sut = _Owner()
    sut.locale = DEFAULT_LOCALE_TAG
    assert sut.locale == DEFAULT_LOCALE


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

    async def test_dump_linked_data__without_locale(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        sut = HasLocale()
        expected = {"locale": "und"}
        actual = await assert_dumps_linked_data(sut)
        assert actual == expected

    async def test_dump_linked_data__with_locale(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        locale = "en-US"
        sut = HasLocale(locale=resolve_locale(locale))
        expected: Mapping[str, Any] = {
            "locale": locale,
        }
        actual = await assert_dumps_linked_data(sut)
        assert actual == expected
