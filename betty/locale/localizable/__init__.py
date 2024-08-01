"""
The localizable API allows objects to be localized at the point of use.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from typing import Any, cast, TypeAlias, Self, final, TYPE_CHECKING
from warnings import warn

from betty.attr import MutableAttr
from betty.json.linked_data import LinkedDataDumpable
from betty.locale import negotiate_locale, to_locale
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.locale.localizer import Localizer
from typing_extensions import override
from betty.serde.dump import dump_default

if TYPE_CHECKING:
    from betty.serde.dump import DumpMapping, Dump
    from betty.project import Project


class Localizable(ABC):
    """
    A localizable object.

    Objects of this type can convert themselves to localized strings at the point of use.
    """

    @abstractmethod
    def localize(self, localizer: Localizer) -> str:
        """
        Localize ``self`` to a human-readable string.
        """
        pass

    @override
    def __str__(self) -> str:
        localized = self.localize(DEFAULT_LOCALIZER)
        warn(
            f'{type(self)} ("{localized}") SHOULD NOT be cast to a string. Instead, call {type(self)}.localize() to ensure it is always formatted in the desired locale.',
            stacklevel=2,
        )
        return localized


class _FormattableLocalizable(Localizable):
    def format(
        self, *format_args: str | Localizable, **format_kwargs: str | Localizable
    ) -> Localizable:
        return format(self, **format_kwargs)


class _CallLocalizable(Localizable):
    def __init__(self, call: Callable[[Localizer], str]):
        self._call = call

    @override
    def localize(self, localizer: Localizer) -> str:
        return self._call(localizer)


def call(call: Callable[[Localizer], str]) -> Localizable:
    """
    Create a new localizable that outputs the callable's return value.
    """
    return _CallLocalizable(call)


class _GettextLocalizable(_FormattableLocalizable):
    def __init__(
        self,
        gettext_method_name: str,
        *gettext_args: Any,
    ) -> None:
        self._gettext_method_name = gettext_method_name
        self._gettext_args = gettext_args

    @override
    def localize(self, localizer: Localizer) -> str:
        return cast(
            str, getattr(localizer, self._gettext_method_name)(*self._gettext_args)
        )


def gettext(message: str) -> _GettextLocalizable:
    """
    Like :py:meth:`gettext.gettext`.

    Positional arguments are identical to those of :py:meth:`gettext.gettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    return _GettextLocalizable("gettext", message)


def _(message: str) -> _GettextLocalizable:
    """
    Like :py:meth:`betty.locale.localizable.gettext`.

    Positional arguments are identical to those of :py:meth:`gettext.gettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    return gettext(message)


def ngettext(message_singular: str, message_plural: str, n: int) -> _GettextLocalizable:
    """
    Like :py:meth:`gettext.ngettext`.

    Positional arguments are identical to those of :py:meth:`gettext.ngettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    return _GettextLocalizable("ngettext", message_singular, message_plural, n)


def pgettext(context: str, message: str) -> _GettextLocalizable:
    """
    Like :py:meth:`gettext.pgettext`.

    Positional arguments are identical to those of :py:meth:`gettext.pgettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    return _GettextLocalizable("pgettext", context, message)


def npgettext(
    context: str, message_singular: str, message_plural: str, n: int
) -> _GettextLocalizable:
    """
    Like :py:meth:`gettext.npgettext`.

    Positional arguments are identical to those of :py:meth:`gettext.npgettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    return _GettextLocalizable(
        "npgettext", context, message_singular, message_plural, n
    )


class _FormattedLocalizable(Localizable):
    def __init__(
        self,
        localizable: Localizable,
        format_args: Sequence[str | Localizable],
        format_kwargs: Mapping[str, str | Localizable],
    ):
        self._localizable = localizable
        self._format_args = format_args
        self._format_kwargs = format_kwargs

    @override
    def localize(self, localizer: Localizer) -> str:
        return self._localizable.localize(localizer).format(
            *(
                format_arg.localize(localizer)
                if isinstance(format_arg, Localizable)
                else format_arg
                for format_arg in self._format_args
            ),
            **{
                format_kwarg_key: format_kwarg.localize(localizer)
                if isinstance(format_kwarg, Localizable)
                else format_kwarg
                for format_kwarg_key, format_kwarg in self._format_kwargs.items()
            },
        )


def format(  # noqa A001
    localizable: Localizable,
    *format_args: str | Localizable,
    **format_kwargs: str | Localizable,
) -> Localizable:
    """
    Perform string formatting.

    The arguments are identical to those of :py:meth:`str.format`.
    """
    return _FormattedLocalizable(localizable, format_args, format_kwargs)


class _PlainStrLocalizable(Localizable):
    def __init__(self, string: str):
        self._string = string

    @override
    def localize(self, localizer: Localizer) -> str:
        return self._string


def plain(string: str) -> Localizable:
    """
    Turns a plain string into a :py:class:`betty.locale.localizable.Localizable` without any actual translations.
    """
    return _PlainStrLocalizable(string)


StaticTranslations: TypeAlias = Mapping[str, str]
"""
Keys are locales, values are translations.
See :py:func:`betty.locale.localizable.assertion.assert_static_translations`.
"""


ShorthandStaticTranslations: TypeAlias = StaticTranslations | str
"""
:py:const:`StaticTranslations` or a string which is the translation for the undetermined locale.
See :py:func:`betty.locale.localizable.assertion.assert_static_translations`.
"""


class StaticTranslationsLocalizable(_FormattableLocalizable, LinkedDataDumpable):
    """
    Provide a :py:class:`betty.locale.localizable.Localizable` backed by static translations.
    """

    _translations: dict[str, str]

    def __init__(
        self,
        translations: ShorthandStaticTranslations | None = None,
        *,
        required: bool = True,
    ):
        """
        :param translations: Keys are locales, values are translations.
        """
        super().__init__()
        self._required = required
        self._translations: dict[str, str]
        if translations is not None:
            self.set(translations)
        else:
            self._translations = {}

    def __getitem__(self, locale: str) -> str:
        return self._translations[locale]

    def __setitem__(self, locale: str, translation: str) -> None:
        self._translations[locale] = translation

    def __len__(self) -> int:
        return len(self._translations)

    def set(self, translations: Self | ShorthandStaticTranslations) -> None:
        """
        Set the translations.
        """
        from betty.assertion import assert_len_min
        from betty.locale.localizable.assertion import assert_static_translations

        if isinstance(translations, StaticTranslationsLocalizable):
            self._translations = translations._translations
        else:
            translations = assert_static_translations()(translations)
            assert_len_min(1 if self._required else 0)(translations)
            self._translations = dict(translations)

    @override
    def localize(self, localizer: Localizer) -> str:
        if len(self._translations) > 1:
            available_locales = tuple(self._translations.keys())
            requested_locale = to_locale(
                (
                    negotiate_locale(localizer.locale, available_locales)
                    or available_locales[0]
                )
            )
            if requested_locale:
                return self._translations[requested_locale]
        elif not self._translations:
            return ""
        return next(iter(self._translations.values()))

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        return dict(self._translations)

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> DumpMapping[Dump]:
        schema = await super().linked_data_schema(project)
        schema["$ref"] = "#/definitions/staticTranslations"
        definitions = dump_default(schema, "definitions", dict)
        if "staticTranslations" not in definitions:
            definitions["staticTranslations"] = {
                "type": "object",
                "description": "Keys are IETF BCP-47 language tags.",
                "additionalProperties": {
                    "type": "string",
                    "description": "A human-readable translation.",
                },
            }
        return schema


def static(translations: ShorthandStaticTranslations) -> Localizable:
    """
    Create a new localizable that outputs the given static translations.
    """
    from betty.locale.localizable.assertion import assert_static_translations

    return StaticTranslationsLocalizable(assert_static_translations()(translations))


@final
class StaticTranslationsLocalizableAttr(
    MutableAttr[object, StaticTranslationsLocalizable, ShorthandStaticTranslations]
):
    """
    An instance attribute that contains :py:class:`betty.locale.localizable.StaticTranslationsLocalizable`.
    """

    def __init__(self, attr_name: str, *, required: bool = True):
        super().__init__(attr_name)
        self._required = required

    @override
    def new_attr(self, instance: object) -> StaticTranslationsLocalizable:
        return StaticTranslationsLocalizable(None, required=self._required)

    @override
    def set_attr(self, instance: object, value: ShorthandStaticTranslations) -> None:
        self.get_attr(instance).set(value)

    @override
    def del_attr(self, instance: object) -> None:
        self.get_attr(instance).set({})
