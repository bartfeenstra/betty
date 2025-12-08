"""
The localizable API allows objects to be localized at the point of use.
"""

from __future__ import annotations

import decimal
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from textwrap import indent
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    Self,
    TypeAlias,
    TypeVar,
    cast,
    final,
    overload,
)
from warnings import warn

from babel import Locale
from typing_extensions import override

from betty.attr import OptionalAttr, RequiredAttr
from betty.data import Key
from betty.locale import (
    LocaleLike,
    ensure_locale,
    negotiate_locale,
    plural_tags,
    to_language_tag,
)
from betty.locale.localized import Localized, LocalizedStr
from betty.locale.localizer import DEFAULT_LOCALIZER, Localizer
from betty.mutability import Mutable

if TYPE_CHECKING:
    from betty.exception import HumanFacingExceptionGroup

_T = TypeVar("_T")


class _Localizable(ABC, Generic[_T]):
    @abstractmethod
    def format(self, **format_kwargs: LocalizableLike) -> _T:
        """
        Apply string formatting to the eventual localized string.

        The arguments are identical to those of :py:meth:`str.format`.

        :return:
            A new localizable object.
        """


class Localizable(_Localizable["Localizable"]):
    """
    A localizable object.

    Objects of this type can convert themselves to localized strings at the point of use.
    """

    @abstractmethod
    def localize(self, localizer: Localizer, /) -> Localized & str:
        """
        Localize ``self`` to a human-readable string.
        """

    @override
    def format(self, **format_kwargs: LocalizableLike) -> Localizable:
        return _FormattedLocalizable(self, format_kwargs)

    @override
    def __str__(self) -> str:
        localized = self.localize(DEFAULT_LOCALIZER)
        warn(
            f'{type(self)} ("{localized}") SHOULD NOT be cast to a string. Instead, call {type(self)}.localize() to ensure it is always formatted in the desired locale.',
            stacklevel=2,
        )
        return localized


LocalizableCount: TypeAlias = int | float | decimal.Decimal
"""
A count to localize strings for.

Based on :py:meth:`babel.plural.PluralRule.__call__`.
"""


class CountableLocalizable(_Localizable["CountableLocalizable"]):
    """
    An object that can be localized for a specific count (number of things).
    """

    @abstractmethod
    def count(self, count: LocalizableCount, /) -> Localizable:
        """
        Create a localizable for the given count (number of things).

        Implementations MUST automatically format the returned localizable with a ``{count}`` argument set to ``count``.
        """

    @override
    def format(self, **format_kwargs: LocalizableLike) -> CountableLocalizable:
        return _FormattedCountableLocalizable(self, format_kwargs)


def do_you_mean(*available_options: str) -> Localizable:
    """
    Produce a message listing available options.
    """
    match len(available_options):
        case 0:
            return _("There are no available options.")
        case 1:
            return _("Do you mean {available_option}?").format(
                available_option=available_options[0]
            )
        case _:
            return _("Do you mean one of {available_options}?").format(
                available_options=AnyEnumeration(*sorted(map(str, available_options)))
            )


class _GettextLocalizable(Localizable):
    def __init__(
        self,
        gettext_method_name: str,
        *gettext_args: Any,
    ) -> None:
        self._gettext_method_name = gettext_method_name
        self._gettext_args = gettext_args

    @override
    def localize(self, localizer: Localizer, /) -> Localized & str:
        return LocalizedStr(
            cast(
                "str",
                getattr(localizer, self._gettext_method_name)(*self._gettext_args),  # type: ignore[operator]
            ),
            locale=localizer.locale,
        )


class _CountableGettextLocalizable(CountableLocalizable):
    def __init__(
        self,
        gettext_method_name: str,
        *gettext_args: Any,
    ) -> None:
        self._gettext_method_name = gettext_method_name
        self._gettext_args = gettext_args

    @override
    def count(self, count: LocalizableCount, /) -> Localizable:
        return _GettextLocalizable(
            self._gettext_method_name, *self._gettext_args, count
        ).format(count=str(count))


def gettext(message: str, /) -> Localizable:
    """
    Like :py:meth:`gettext.gettext`.

    Positional arguments are identical to those of :py:meth:`gettext.gettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    return _GettextLocalizable("gettext", message)


def _(message: str, /) -> Localizable:
    """
    Like :py:meth:`betty.locale.localizable.gettext`.

    Positional arguments are identical to those of :py:meth:`gettext.gettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    return gettext(message)


@overload
def ngettext(message_singular: str, message_plural: str, n: int, /) -> Localizable:
    pass


@overload
def ngettext(
    message_singular: str, message_plural: str, n: None = None, /
) -> CountableLocalizable:
    pass


def ngettext(
    message_singular: str, message_plural: str, n: int | None = None, /
) -> Localizable | CountableLocalizable:
    """
    Like :py:meth:`gettext.ngettext`.

    Positional arguments are identical to those of :py:meth:`gettext.ngettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.

    Messages MUST have a ``{count}`` placeholder.
    """
    if n is None:
        return _CountableGettextLocalizable(
            "ngettext", message_singular, message_plural
        )
    return _GettextLocalizable("ngettext", message_singular, message_plural, n).format(
        count=str(n)
    )


def pgettext(context: str, message: str, /) -> Localizable:
    """
    Like :py:meth:`gettext.pgettext`.

    Positional arguments are identical to those of :py:meth:`gettext.pgettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    return _GettextLocalizable("pgettext", context, message)


@overload
def npgettext(
    context: str, message_singular: str, message_plural: str, n: int, /
) -> Localizable:
    pass


@overload
def npgettext(
    context: str, message_singular: str, message_plural: str, n: None = None, /
) -> CountableLocalizable:
    pass


def npgettext(
    context: str, message_singular: str, message_plural: str, n: int | None = None, /
) -> Localizable | CountableLocalizable:
    """
    Like :py:meth:`gettext.npgettext`.

    Positional arguments are identical to those of :py:meth:`gettext.npgettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    if n is None:
        return _CountableGettextLocalizable(
            "npgettext", context, message_singular, message_plural
        )
    return _GettextLocalizable(
        "npgettext", context, message_singular, message_plural, n
    ).format(count=str(n))


class _FormattedLocalizable(Localizable):
    def __init__(
        self,
        localizable: Localizable,
        format_kwargs: Mapping[str, LocalizableLike],
        /,
    ):
        self._localizable = localizable
        self._format_kwargs = dict(format_kwargs)

    @override
    def format(self, **format_kwargs: LocalizableLike) -> Localizable:
        self._format_kwargs.update(format_kwargs)
        return self

    @override
    def localize(self, localizer: Localizer, /) -> Localized & str:
        return LocalizedStr(
            self._localizable.localize(localizer).format(
                **{
                    format_kwarg_key: format_kwarg.localize(localizer)
                    if isinstance(format_kwarg, Localizable)
                    else format_kwarg
                    for format_kwarg_key, format_kwarg in self._format_kwargs.items()
                },
            )
        )


class _FormattedCountableLocalizable(CountableLocalizable):
    def __init__(
        self,
        localizable: CountableLocalizable,
        format_kwargs: Mapping[str, LocalizableLike],
        /,
    ):
        self._localizable = localizable
        self._format_kwargs = format_kwargs

    @override
    def count(self, count: LocalizableCount, /) -> Localizable:
        return _FormattedLocalizable(
            self._localizable.count(count),
            {**self._format_kwargs, "count": str(count)},
        )


@final
class Plain(Localizable):
    """
    Turns a plain string into a :py:class:`betty.locale.localizable.Localizable` without any actual translations.
    """

    def __init__(self, text: str, locale: LocaleLike | None = None, /):
        from betty.assertion import assert_str

        assert_str(minimum_length=1)(text)
        self._text = text
        self._locale = None if locale is None else ensure_locale(locale)

    @property
    def text(self) -> str:
        """
        The plain text.
        """
        return self._text

    @property
    def locale(self) -> Locale | None:
        """
        The locale the text is in.
        """
        return self._locale

    @override
    def localize(self, localizer: Localizer, /) -> Localized & str:
        return LocalizedStr(self._text, locale=self._locale)


CountableStaticTranslationsMapping: TypeAlias = Mapping[Locale, Mapping[str, str]]
"""
Countable static translations for :py:class:`betty.locale.localizable.CountableStaticTranslations`.

Values are mappings of locales to mappings of CLDR plural tags to translations.

See :py:func:`betty.locale.localizable.assertion.assert_countable_static_translations`.
"""

ShorthandCountableStaticTranslations: TypeAlias = Mapping[LocaleLike, Mapping[str, str]]
"""
Static translations for :py:class:`betty.locale.localizable.StaticTranslations`.

Values are mappings of locales or language tags to mappings of CLDR plural tags to translations.

See :py:func:`betty.locale.localizable.assertion.assert_static_translations`.
"""


@final
class CountableStaticTranslations(CountableLocalizable):
    """
    A countable localizable backed by static translations.
    """

    _translations: CountableStaticTranslationsMapping

    def __init__(self, translations: ShorthandCountableStaticTranslations, /):
        from betty.assertion import assert_len
        from betty.exception import HumanFacingExceptionGroup

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
                        from betty.locale.localizable.error import (
                            MissingPluralPlaceholder,
                        )

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
                from betty.locale.localizable.error import InvalidPluralTag

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
                from betty.locale.localizable.error import MissingPluralTag

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


StaticTranslationsMapping: TypeAlias = Mapping[Locale | None, str]
"""
Static translations for :py:class:`betty.locale.localizable.StaticTranslations`.

Values are a string, or a mapping of locales to translations.

See :py:func:`betty.locale.localizable.assertion.assert_static_translations`.
"""


ShorthandStaticTranslations: TypeAlias = Mapping[LocaleLike | None, str] | str
"""
Static translations for :py:class:`betty.locale.localizable.StaticTranslations`.

Values are a string, or a mapping of locales or language tags to translations.

See :py:func:`betty.locale.localizable.assertion.assert_static_translations`.
"""


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
    def localize(self, localizer: Localizer, /) -> Localized & str:
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


class LocalizableSequence(ABC):
    """
    A sequence of localizables.
    """

    @property
    @abstractmethod
    def localizables(self) -> Sequence[Localizable]:
        """
        The localizables.
        """


class _LocalizableSequence(LocalizableSequence):
    def __init__(self, *localizables: LocalizableLike):
        self._localizables = tuple(map(ensure_localizable, localizables))

    @override
    @property
    def localizables(self) -> Sequence[Localizable]:
        return self._localizables


class _Join(_LocalizableSequence, Localizable):
    _SEPARATOR: ClassVar[str]

    @override
    def localize(self, localizer: Localizer, /) -> Localized & str:
        return LocalizedStr(
            self._SEPARATOR.join(
                localized
                for part in self.localizables
                if (localized := part.localize(localizer))
            ),
            locale=localizer.locale,
        )


@final
class Chain(_Join):
    """
    Chain multiple localizables together, back to back.
    """

    _SEPARATOR = ""


@final
class Paragraph(_Join):
    """
    Represent multiple localizables as a single paragraph of text.
    """

    _SEPARATOR = " "


@final
class Lines(_Join):
    """
    Represent multiple localizables as multiple lines of text.
    """

    _SEPARATOR = "\n"


@final
class Paragraphs(_Join):
    """
    Represent multiple localizables as multiple paragraphs of text.
    """

    _SEPARATOR = "\n\n"


class _List(_LocalizableSequence, Localizable):
    _TEMPLATE_LEFT_TO_RIGHT = "{prefix} {localized}"
    _TEMPLATE_RIGHT_TO_LEFT = "{localized} {prefix}"

    @override
    def localize(self, localizer: Localizer, /) -> Localized & str:
        if not self.localizables:
            return LocalizedStr("")
        localizeds = []
        prefixes = []
        prefix_lengths = []
        if localizer.locale.character_order == "right-to-left":
            template = self._TEMPLATE_RIGHT_TO_LEFT
        else:
            template = self._TEMPLATE_LEFT_TO_RIGHT
        for index, localizable in enumerate(self._localizables):
            localizeds.append(localizable.localize(localizer))
            prefix = self._get_prefix(localizer, index)
            prefixes.append(prefix)
            prefix_lengths.append(len(prefix))
        max_prefix_length = max(prefix_lengths) + 1
        return LocalizedStr(
            "\n".join(
                template.format(
                    localized=indent(localized, " " * max_prefix_length)[
                        len(prefixes[index]) + 1 :
                    ],
                    prefix=self._get_prefix(localizer, index),
                )
                for index, localized in enumerate(localizeds)
            )
        )

    @abstractmethod
    def _get_prefix(self, localizer: Localizer, index: int, /) -> str:
        pass


@final
class OrderedList(_List):
    """
    Represent multiple localizables in an ordered list.
    """

    _PREFIX_TEMPLATE_LEFT_TO_RIGHT = "{index}."
    _PREFIX_TEMPLATE_RIGHT_TO_LEFT = ".{index}"

    @override
    def _get_prefix(self, localizer: Localizer, index: int, /) -> str:
        if localizer.locale.character_order == "right-to-left":
            template = self._PREFIX_TEMPLATE_RIGHT_TO_LEFT
        else:
            template = self._PREFIX_TEMPLATE_LEFT_TO_RIGHT
        return template.format(index=index + 1)


@final
class UnorderedList(_List):
    """
    Represent multiple localizables in an unordered list.
    """

    @override
    def _get_prefix(self, localizer: Localizer, index: int, /) -> str:
        return "-"


class _Enumeration(_LocalizableSequence, Localizable):
    _LOCALIZABLE: ClassVar[Localizable]

    @override
    def localize(self, localizer: Localizer, /) -> Localized & str:
        if len(self.localizables) == 0:
            return LocalizedStr("")
        if len(self.localizables) == 1:
            return self.localizables[0].localize(localizer)
        return self._LOCALIZABLE.format(
            most=", ".join(
                part.localize(localizer) for part in self.localizables[0:-1]
            ),
            last=self.localizables[-1],
        ).localize(localizer)


@final
class AnyEnumeration(_Enumeration):
    """
    An enumeration where any of the localizables may be applicable.
    """

    _LOCALIZABLE = _("{most}, or {last}")


@final
class AllEnumeration(_Enumeration):
    """
    An enumeration where all of the localizables are applicable.
    """

    _LOCALIZABLE = _("{most}, and {last}")


LocalizableLike: TypeAlias = Localizable | ShorthandStaticTranslations
"""
A localizable, or a type that can be converted into a localizable with :py:func:`betty.locale.localizable.ensure_localizable`.
"""

CountableLocalizableLike: TypeAlias = (
    CountableLocalizable | ShorthandCountableStaticTranslations
)
"""
A countable localizable, or a type that can be converted into a countable localizable with :py:func:`betty.locale.localizable.ensure_countable_localizable`.
"""


def ensure_localizable(localizable: LocalizableLike) -> Localizable:
    """
    Ensure that a localizable-like value is or is made to be an actual localizable.
    """
    if isinstance(localizable, Localizable):
        return localizable
    if isinstance(localizable, str):
        return Plain(localizable)
    return StaticTranslations(localizable)


def ensure_countable_localizable(
    localizable: CountableLocalizableLike,
) -> CountableLocalizable:
    """
    Ensure that a countable-localizable-like value is or is made to be an actual countable localizable.
    """
    if isinstance(localizable, CountableLocalizable):
        return localizable
    return CountableStaticTranslations(localizable)


@final
class RequiredLocalizableAttr(RequiredAttr[Localizable]):
    """
    An attribute for a required :py:class:`betty.locale.localizable.Localizable`.
    """

    def __set__(self, instance: object, value: LocalizableLike, /) -> None:
        setattr(instance, self._attr_name, ensure_localizable(value))


@final
class OptionalLocalizableAttr(OptionalAttr[Localizable | None]):
    """
    An attribute for an optional :py:class:`betty.locale.localizable.Localizable`.
    """

    def __set__(self, instance: object, value: LocalizableLike | None, /) -> None:
        setattr(
            instance,
            self._attr_name,
            None if value is None else ensure_localizable(value),
        )

    def __delete__(self, instance: object) -> None:
        setattr(instance, self._attr_name, None)


@final
class RequiredCountableLocalizableAttr(RequiredAttr[CountableLocalizable]):
    """
    An attribute for a required :py:class:`betty.locale.localizable.CountableLocalizable`.
    """

    def __set__(
        self, instance: object, value: CountableLocalizableLike | None, /
    ) -> None:
        setattr(
            instance,
            self._attr_name,
            None if value is None else ensure_countable_localizable(value),
        )
