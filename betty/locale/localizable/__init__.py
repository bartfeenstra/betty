"""
The localizable API allows objects to be localized at the point of use.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import (
    Callable,
    Iterable,
    Mapping,
    MutableMapping,
    Sequence,
)
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

from typing_extensions import override

from betty.json.linked_data import LinkedDataDumpableWithSchema
from betty.json.schema import Object
from betty.locale import UNDETERMINED_LOCALE, negotiate_locale, to_locale
from betty.locale.localized import Localized, LocalizedStr
from betty.locale.localizer import DEFAULT_LOCALIZER, Localizer
from betty.mutability import Mutable
from betty.serde.dump import Dump, DumpMapping

if TYPE_CHECKING:
    from betty.project import Project


_T = TypeVar("_T")


class _Localizable(Generic[_T], ABC):
    @abstractmethod
    def format(self, **format_kwargs: str | Localizable) -> _T:
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
    def localize(self, localizer: Localizer) -> Localized & str:
        """
        Localize ``self`` to a human-readable string.
        """

    @override
    def format(self, **format_kwargs: str | Localizable) -> Localizable:
        return _FormattedLocalizable(self, format_kwargs)

    @override
    def __str__(self) -> str:
        localized = self.localize(DEFAULT_LOCALIZER)
        warn(
            f'{type(self)} ("{localized}") SHOULD NOT be cast to a string. Instead, call {type(self)}.localize() to ensure it is always formatted in the desired locale.',
            stacklevel=2,
        )
        return localized


class CountableLocalizable(_Localizable["CountableLocalizable"]):
    """
    An object that can be localized for a specific count (number of things).
    """

    @abstractmethod
    def count(self, count: int) -> Localizable:
        """
        Create a localizable for the given count (number of things).

        Implementations MUST automatically format the returned localizable with a ``{count}`` argument set to ``count``.
        """

    @override
    def format(self, **format_kwargs: str | Localizable) -> CountableLocalizable:
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
                available_options=AnyEnumeration(*sorted(available_options))
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
    def localize(self, localizer: Localizer) -> Localized & str:
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
    def count(self, count: int) -> Localizable:
        return _GettextLocalizable(
            self._gettext_method_name, *self._gettext_args, count
        ).format(count=str(count))


def gettext(message: str) -> Localizable:
    """
    Like :py:meth:`gettext.gettext`.

    Positional arguments are identical to those of :py:meth:`gettext.gettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    return _GettextLocalizable("gettext", message)


def _(message: str) -> Localizable:
    """
    Like :py:meth:`betty.locale.localizable.gettext`.

    Positional arguments are identical to those of :py:meth:`gettext.gettext`.
    Keyword arguments are identical to those of :py:met:`str.format`, except that
    any :py:class:`betty.locale.localizable.Localizable` will be localized before string
    formatting.
    """
    return gettext(message)


@overload
def ngettext(message_singular: str, message_plural: str, n: int) -> Localizable:
    pass


@overload
def ngettext(
    message_singular: str, message_plural: str, n: None = None
) -> CountableLocalizable:
    pass


def ngettext(
    message_singular: str, message_plural: str, n: int | None = None
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


def pgettext(context: str, message: str) -> Localizable:
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
    context: str, message_singular: str, message_plural: str, n: int
) -> Localizable:
    pass


@overload
def npgettext(
    context: str, message_singular: str, message_plural: str, n: None = None
) -> CountableLocalizable:
    pass


def npgettext(
    context: str, message_singular: str, message_plural: str, n: int | None = None
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
        self, localizable: Localizable, format_kwargs: Mapping[str, str | Localizable]
    ):
        self._localizable = localizable
        self._format_kwargs = dict(format_kwargs)

    @override
    def format(self, **format_kwargs: str | Localizable) -> Localizable:
        self._format_kwargs.update(format_kwargs)
        return self

    @override
    def localize(self, localizer: Localizer) -> Localized & str:
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
        format_kwargs: Mapping[str, str | Localizable],
    ):
        self._localizable = localizable
        self._format_kwargs = format_kwargs

    @override
    def count(self, count: int) -> Localizable:
        return _FormattedLocalizable(
            self._localizable.count(count),
            {**self._format_kwargs, "count": str(count)},
        )


@final
class Plain(Localizable):
    """
    Turns a plain string into a :py:class:`betty.locale.localizable.Localizable` without any actual translations.
    """

    def __init__(self, string: str, locale: str = UNDETERMINED_LOCALE):
        self._string = string
        self._locale = locale

    @override
    def localize(self, localizer: Localizer) -> Localized & str:
        return LocalizedStr(self._string, locale=self._locale)


@final
class CountablePlain(CountableLocalizable):
    """
    Turn plain strings into a :py:class:`betty.locale.localizable.CountableLocalizable` without any actual translations.
    """

    def _default_is_plural(self, count: int) -> bool:
        # This mimics Python's built-in gettext module.
        return count != 1

    def __init__(
        self,
        string_singular: str,
        string_plural: str,
        *,
        locale: str = UNDETERMINED_LOCALE,
        is_plural: Callable[[int], bool] | None = None,
    ):
        self._string_singular = Plain(string_singular, locale=locale)
        self._string_plural = Plain(string_plural, locale=locale)
        self._is_plural = is_plural or self._default_is_plural

    @override
    def count(self, count: int) -> Localizable:
        return self._string_plural if self._is_plural(count) else self._string_singular


StaticTranslationsMapping: TypeAlias = Mapping[str, str]
"""
Keys are locales, values are translations.

See :py:func:`betty.locale.localizable.assertion.assert_static_translations`.
"""


ShorthandStaticTranslations: TypeAlias = StaticTranslationsMapping | str
"""
:py:const:`StaticTranslations` or a string which is the translation for the undetermined locale.

See :py:func:`betty.locale.localizable.assertion.assert_static_translations`.
"""


class StaticTranslationsSchema(Object):
    """
    A JSON Schema for :py:class:`betty.locale.localizable.StaticTranslations`.
    """

    def __init__(
        self, *, title: str = "Static translations", description: str | None = None
    ):
        super().__init__(
            title=title,
            description=(
                (description or "") + "Keys are IETF BCP-47 language tags."
            ).strip(),
        )
        self._schema["additionalProperties"] = {
            "type": "string",
            "description": "A human-readable translation.",
        }


class StaticTranslations(
    Mutable, Localizable, LinkedDataDumpableWithSchema[Object, DumpMapping[Dump]]
):
    """
    Provide a :py:class:`betty.locale.localizable.Localizable` backed by static translations.
    """

    _translations: MutableMapping[str, str]

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
        if translations is not None:
            self.replace(translations)
        else:
            self._translations = {}

    def __getitem__(self, locale: str) -> str:
        return self._translations[locale]

    def __setitem__(self, locale: str, translation: str) -> None:
        self.assert_mutable()
        self._translations[locale] = translation

    def __len__(self) -> int:
        return len(self._translations)

    def replace(self, translations: Self | ShorthandStaticTranslations) -> None:
        """
        Replace the translations.
        """
        from betty.assertion import assert_len
        from betty.locale.localizable.assertion import assert_static_translations

        self.assert_mutable()
        if isinstance(translations, StaticTranslations):
            self._translations = translations._translations
        else:
            translations = assert_static_translations()(translations)
            assert_len(minimum=1 if self._required else 0)(translations)
            self._translations = dict(translations)

    @property
    def translations(self) -> StaticTranslationsMapping:
        """
        The translations.
        """
        return dict(self._translations)

    @override
    def localize(self, localizer: Localizer) -> Localized & str:
        if len(self._translations) > 1:
            available_locales = tuple(self._translations.keys())
            requested_locale = to_locale(
                negotiate_locale(localizer.locale, available_locales)
                or available_locales[0]
            )
            if requested_locale:
                return LocalizedStr(
                    self._translations[requested_locale], locale=requested_locale
                )
        elif not self._translations:
            return LocalizedStr("")
        locale, translation = next(iter(self._translations.items()))
        return LocalizedStr(translation, locale=locale)

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        return {**self._translations}

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        return StaticTranslationsSchema()

    @classmethod
    def from_localizable(
        cls,
        other: Localizable,
        localizers: Iterable[Localizer],
        *,
        required: bool = True,
    ) -> Self:
        """
        Create a new instance from another :py:class`betty.locale.localizable.Localizable`.
        """
        if type(other) is cls:
            return other
        return cls(
            {
                localizer.locale: other.localize(localizer=localizer)
                for localizer in localizers
            },
            required=required,
        )

    @classmethod
    async def dump_linked_data_for(
        cls, project: Project, other: Localizable
    ) -> DumpMapping[Dump]:
        """
        Dump a :py:class:`betty.locale.localizable.Localizable` to `JSON-LD <https://json-ld.org/>`_.
        """
        localizers = await project.localizers
        return await StaticTranslations.from_localizable(
            other, [localizers.get(locale) for locale in project.configuration.locales]
        ).dump_linked_data(project)


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
    def __init__(self, *localizables: Localizable | str):
        self._localizables = tuple(
            localizable if isinstance(localizable, Localizable) else Plain(localizable)
            for localizable in localizables
        )

    @override
    @property
    def localizables(self) -> Sequence[Localizable]:
        return self._localizables


class _Join(_LocalizableSequence, Localizable):
    _SEPARATOR: ClassVar[str]

    @override
    def localize(self, localizer: Localizer) -> Localized & str:
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
    def localize(self, localizer: Localizer) -> Localized & str:
        if not self.localizables:
            return LocalizedStr("")
        localizeds = []
        prefixes = []
        prefix_lengths = []
        if localizer.locale_data.character_order == "right-to-left":
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
    def _get_prefix(self, localizer: Localizer, index: int) -> str:
        pass


@final
class OrderedList(_List):
    """
    Represent multiple localizables in an ordered list.
    """

    _PREFIX_TEMPLATE_LEFT_TO_RIGHT = "{index}."
    _PREFIX_TEMPLATE_RIGHT_TO_LEFT = ".{index}"

    @override
    def _get_prefix(self, localizer: Localizer, index: int) -> str:
        if localizer.locale_data.character_order == "right-to-left":
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
    def _get_prefix(self, localizer: Localizer, index: int) -> str:
        return "-"


class _Enumeration(_LocalizableSequence, Localizable):
    _LOCALIZABLE: ClassVar[Localizable]

    @override
    def localize(self, localizer: Localizer) -> Localized & str:
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
