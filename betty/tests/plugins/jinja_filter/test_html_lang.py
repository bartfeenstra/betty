from gettext import NullTranslations

import pytest
from babel import Locale

from betty.document import Document
from betty.locale import HasLocaleStr
from betty.locale.localize import Localizer
from betty.test_utils.conftest import AssertTemplateString


class TestHtmlLang:
    @pytest.mark.parametrize(
        ("expected", "autoescape", "has_locale", "localizer_locale"),
        [
            ("Hallo, wereld!", True, "Hallo, wereld!", "nl"),
            ("Hallo, wereld!", True, "Hallo, wereld!", "ar"),
            (
                "Hallo, wereld!",
                True,
                HasLocaleStr("Hallo, wereld!", locale=Locale("nl")),
                "nl",
            ),
            (
                "Hallo, wereld!",
                False,
                HasLocaleStr("Hallo, wereld!", locale=Locale("nl")),
                "nl",
            ),
            (
                '<span lang="nl">Hallo, wereld!</span>',
                True,
                HasLocaleStr("Hallo, wereld!", locale=Locale("nl")),
                "en",
            ),
            (
                '<span lang="nl">Hallo, wereld!</span>',
                False,
                HasLocaleStr("Hallo, wereld!", locale=Locale("nl")),
                "en",
            ),
            (
                '<span lang="nl" dir="ltr">Hallo, wereld!</span>',
                True,
                HasLocaleStr("Hallo, wereld!", locale=Locale("nl")),
                "ar",
            ),
            (
                '<span lang="nl" dir="ltr">Hallo, wereld!</span>',
                False,
                HasLocaleStr("Hallo, wereld!", locale=Locale("nl")),
                "ar",
            ),
        ],
    )
    async def test___call__(
        self,
        assert_template_string: AssertTemplateString,
        expected: str,
        autoescape: bool,
        has_locale: str,
        localizer_locale: str,
    ) -> None:
        template = "{{ has_locale | html_lang }}"
        async with assert_template_string(
            template=template,
            data={
                "has_locale": has_locale,
                "document": Document(
                    localizer=Localizer(localizer_locale, NullTranslations())
                ),
            },
            autoescape=autoescape,
        ) as (actual, _):
            assert actual == expected
