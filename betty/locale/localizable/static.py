"""
Static translations.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Self, final, override

from betty.assertions.if_else import assert_if_else
from betty.assertions.locale import assert_locale
from betty.assertions.mapping import assert_mapping
from betty.assertions.str import assert_str
from betty.exception import reraise_with_indicator
from betty.indicator.selector import Key
from betty.locale import (
    LocalizedStr,
    ResolvableLocale,
    negotiate_locale,
    plural_tags,
    resolve_locale,
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
from betty.portable import Portable, PortableData

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from babel import Locale

    from betty.locale.localize import Localizer
    from betty.typing import Intersection as Intersection


@final
class CountableStaticTranslations(CountableLocalizable, Portable):
    """
    A countable localizable backed by static translations.
    """

    _translations: CountableStaticTranslationsMapping

    def __init__(self, translations: ShorthandCountableStaticTranslations, /):
        from betty.assertions.len import assert_len

        assert_len(minimum=1)(translations)
        self._translations = {
            self._ensure_locale(locale, locale_translations): locale_translations
            for locale, locale_translations in translations.items()
        }

    @property
    def translations(self) -> CountableStaticTranslationsMapping:
        """
        The translations.
        """
        return dict(self._translations)

    def _ensure_locale(
        self, locale: ResolvableLocale, translations: Mapping[str, str]
    ) -> Locale:
        from betty.assertions.len import assert_len

        locale = resolve_locale(locale)
        with reraise_with_indicator(Key(to_language_tag(locale))):
            for plural_tag, translation in translations.items():
                with reraise_with_indicator(Key(plural_tag)):
                    assert_len(minimum=1)(translations)
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
        return UnorderedList(*[
            f"{plural_tag}: {translation}"
            for plural_tag, translation in translations.items()
        ])

    @override
    def count(self, count: LocalizableCount, /) -> Localizable:
        return StaticTranslations({
            locale: self._translations[locale][locale.plural_form(count)]
            for locale in self._translations
        }).format(count=str(count))

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        return cls(
            assert_mapping(
                assert_mapping(
                    assert_str(),
                    assert_str(),
                ),
                assert_locale(),
            )(portable)
        )

    @override
    def dump(self) -> PortableData:
        return {
            to_language_tag(locale): translations
            for locale, translations in self.translations.items()
        }  # ty:ignore[invalid-return-type]


@final
class StaticTranslations(Localizable, Portable):
    """
    A localizable backed by static translations.

    All configuration options
    -------------------------

    This configuration is either a single translation as a string,
    or multiple translations as a key-value mapping.

    A single translation
    ^^^^^^^^^^^^^^^^^^^^

    .. list-table::
       :align: left
       :stub-columns: 1

       * -  Type
         -  string

    A single translation can be set that is to be used for all languages.

    Example configuration:

    .. tab-set::

       .. tab-item:: YAML

          .. code-block:: yaml

              "I am a single translation, used for all languages"

       .. tab-item:: JSON

          .. code-block:: json

              "I am a single translation, used for all languages"

    Multiple translations
    ^^^^^^^^^^^^^^^^^^^^^

    .. list-table::
       :align: left
       :stub-columns: 1

       * -  Type
         -  mapping
                Keys (string) are `IETF BCP 47 language tags <https://en.wikipedia.org/wiki/IETF_language_tag>`_,
                and values (string) are human-readable translations.

    Example configuration:

    .. tab-set::

       .. tab-item:: YAML

          .. code-block:: yaml

              en-US: "I'm the English translation"
              nl-NL: "Ik ben de Nederlandse vertaling"

       .. tab-item:: JSON

          .. code-block:: json

              {
                "en-US": "I'm the English translation",
                "nl-NL": "Ik ben de Nederlandse vertaling",
              }
    """

    _translations: StaticTranslationsMapping

    def __init__(self, translations: ShorthandStaticTranslations, /):
        """
        :param translations: Keys are locales, values are translations.
        """
        from betty.assertions.len import assert_len

        super().__init__()
        assert_len(minimum=1)(translations)
        self._translations = (
            {None: translations}
            if isinstance(translations, str)
            else {
                None if locale is None else resolve_locale(locale): translation
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
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        if len(self._translations) > 1:
            available_locales = tuple(filter(None, self._translations.keys()))
            negotiated_locale = negotiate_locale(localizer.locale, available_locales)
            if negotiated_locale is not None:
                return LocalizedStr(
                    self._translations[negotiated_locale], locale=negotiated_locale
                )
        locale, translation = next(iter(self._translations.items()))
        return LocalizedStr(translation, locale=locale)

    @classmethod
    def resolve(cls, other: Localizable, localizers: Iterable[Localizer], /) -> Self:
        """
        Create a new instance from another :py:class`betty.locale.localizable.Localizable`.
        """
        if type(other) is cls:
            return other  # ty:ignore[invalid-return-type]
        return cls({
            localizer.locale: other.localize(localizer) for localizer in localizers
        })

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        return cls(
            assert_if_else(
                assert_str().pipe(lambda translation: {None: translation}),
                assert_mapping(assert_str(), assert_locale()),
            )(portable)
        )

    @override
    def dump(self) -> PortableData:
        if len(self.translations) == 1:
            with suppress(KeyError):
                # Explicitly cast to a string because pyyaml cannot dump ``str`` subclasses.
                return str(self.translations[None])
        return {
            # Explicitly cast to a string because pyyaml cannot dump ``str`` subclasses.
            to_language_tag(locale): str(translation)
            for locale, translation in self.translations.items()
        }
