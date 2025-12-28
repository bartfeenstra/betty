"""
Static translations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.data import Key
from betty.exception import HumanFacingExceptionGroup
from betty.locale import (
    HasLocale,
    HasLocaleStr,
    LocaleLike,
    ensure_locale,
    negotiate_locale,
    plural_tags,
    to_language_tag,
)
from betty.locale.localizable import (
    CountableLocalizable,
    CountableStaticTranslationsMapping,
    Localizable,
    LocalizableCount,
    ShorthandCountableStaticTranslations,
    ShorthandStaticTranslations,
    StaticTranslationsMapping,
)
from betty.locale.localizable.error import (
    InvalidPluralTag,
    MissingPluralPlaceholder,
    MissingPluralTag,
)
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import (
    AllEnumeration,
    Paragraphs,
    UnorderedList,
    do_you_mean,
)
from betty.mutability import Mutable

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from babel import Locale

    from betty.locale.localize import Localizer


@final
class CountableStaticTranslations(CountableLocalizable):
    """
    A countable localizable backed by static translations.
    """

    _translations: CountableStaticTranslationsMapping

    def __init__(self, translations: ShorthandCountableStaticTranslations, /):
        from betty.assertion import assert_len

        assert_len(minimum=1)(translations)
        with HumanFacingExceptionGroup() as errors:
            self._translations = {
                self._ensure_locale(
                    locale, locale_translations, errors
                ): locale_translations
                for locale, locale_translations in translations.items()
            }

    @property
    def translations(self) -> CountableStaticTranslationsMapping:
        """
        The translations.
        """
        return dict(self._translations)

    def _ensure_locale(
        self,
        locale: LocaleLike,
        translations: Mapping[str, str],
        errors: HumanFacingExceptionGroup,
    ) -> Locale:
        from betty.assertion import assert_len

        locale = ensure_locale(locale)
        with errors.absorb(Key(to_language_tag(locale))):
            for plural_tag, translation in translations.items():
                plural_tag_key = Key(plural_tag)
                with errors.absorb(plural_tag_key):
                    assert_len(minimum=1)(translations)
                with errors.absorb(plural_tag_key):
                    if "{count}" not in translation:
                        raise MissingPluralPlaceholder(
                            Paragraphs(
                                _(
                                    "Missing `{{count}}` placeholder in {locale} plural translations"
                                ).format(locale=to_language_tag(locale)),
                                self._format_translations(translations),
                            )
                        )
            provided_plural_tags = set(translations.keys())
            locale_plural_tags = set(plural_tags(locale))
            invalid_plural_tags = provided_plural_tags - locale_plural_tags
            missing_plural_tags = locale_plural_tags - provided_plural_tags
            if invalid_plural_tags:
                raise InvalidPluralTag(
                    Paragraphs(
                        _(
                            "Invalid plural tag(s) {plural_tags} for {locale} translations."
                        ).format(
                            locale=to_language_tag(locale),
                            plural_tags=AllEnumeration(
                                *self._format_plural_tags(invalid_plural_tags)
                            ),
                        ),
                        do_you_mean(*self._format_plural_tags(locale_plural_tags)),
                        self._format_translations(translations),
                        self._format_plural_rules_link(locale),
                    )
                )
            if missing_plural_tags:
                raise MissingPluralTag(
                    Paragraphs(
                        _(
                            "Missing plural tag(s) {plural_tags} for {locale} translations."
                        ).format(
                            locale=to_language_tag(locale),
                            plural_tags=AllEnumeration(
                                *self._format_plural_tags(missing_plural_tags)
                            ),
                        ),
                        self._format_translations(translations),
                        self._format_plural_rules_link(locale),
                    )
                )
            return locale

    def _format_plural_tags(self, plural_tags: Iterable[str]) -> Iterable[str]:
        return [f'"{plural_tag}"' for plural_tag in sorted(plural_tags)]

    def _format_plural_rules_link(self, locale: Locale) -> Localizable:
        return _("Read more at {url}").format(
            url=f"https://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html#{locale}"
        )

    def _format_translations(self, translations: Mapping[str, str]) -> Localizable:
        return UnorderedList(
            *[
                f"{plural_tag}: {translation}"
                for plural_tag, translation in translations.items()
            ]
        )

    @override
    def count(self, count: LocalizableCount, /) -> Localizable:
        return StaticTranslations(
            {
                locale: self._translations[locale][locale.plural_form(count)]
                for locale in self._translations
            }
        ).format(count=str(count))


@final
class StaticTranslations(Mutable, Localizable):
    """
    A localizable backed by static translations.
    """

    _translations: StaticTranslationsMapping

    def __init__(self, translations: ShorthandStaticTranslations, /):
        """
        :param translations: Keys are locales, values are translations.
        """
        from betty.assertion import assert_len

        super().__init__()
        assert_len(minimum=1)(translations)
        self._translations = (
            {None: translations}
            if isinstance(translations, str)
            else {
                None if locale is None else ensure_locale(locale): translation
                for locale, translation in translations.items()
            }
        )
        assert len(self._translations) > 0

    @property
    def translations(self) -> StaticTranslationsMapping:
        """
        The translations.
        """
        return dict(self._translations)

    @override
    def localize(self, localizer: Localizer, /) -> HasLocale & str:
        if len(self._translations) > 1:
            available_locales = tuple(filter(None, self._translations.keys()))
            negotiated_locale = negotiate_locale(localizer.locale, available_locales)
            if negotiated_locale is not None:
                return HasLocaleStr(
                    self._translations[negotiated_locale], locale=negotiated_locale
                )
        locale, translation = next(iter(self._translations.items()))
        return HasLocaleStr(translation, locale=locale)

    @classmethod
    def from_localizable(
        cls, other: Localizable, localizers: Iterable[Localizer], /
    ) -> Self:
        """
        Create a new instance from another :py:class`betty.locale.localizable.Localizable`.
        """
        if type(other) is cls:
            return other
        return cls(
            {localizer.locale: other.localize(localizer) for localizer in localizers}
        )
