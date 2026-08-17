"""
Localizable data.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, final, override

from betty.assertions.if_else import assert_if_else
from betty.assertions.locale import assert_locale
from betty.assertions.mapping import assert_mapping
from betty.assertions.str import assert_str
from betty.classtools import Singleton
from betty.data import DataDefinition
from betty.importlib import fully_qualified_name
from betty.locale import to_language_tag
from betty.localizable import CountableLocalizable, Localizable
from betty.localizables.gettext import _
from betty.localizables.plain import Plain
from betty.localizables.static import CountableStaticTranslations, StaticTranslations
from betty.portable import Porter
from betty.portable.error import NotDumpable

if TYPE_CHECKING:
    from betty.portable import PortableData


@final
class LocalizableDefinition(DataDefinition[Localizable], Singleton):
    """
    The data definition for :py:class:`betty.localizable.Localizable`.
    """

    def __init__(self):
        super().__init__(
            cls=Localizable,
            label=_("A localizable string"),
            porter=_LocalizablePorter(),
        )


class _LocalizablePorter(Porter[StaticTranslations]):
    load = override(
        assert_if_else(
            assert_str().pipe(lambda translation: {None: translation}),
            assert_mapping(assert_str(), assert_locale()),
        )
        | StaticTranslations
    )

    @override
    def dump(self, data: Localizable) -> PortableData:
        if isinstance(data, Plain):
            data = StaticTranslations({data.locale: data.text})
        if not isinstance(data, StaticTranslations):
            raise NotDumpable(
                Plain(
                    "Only static translations and plain text can be dumped to portable data, not `{localizable}` objects."
                ).format(localizable=fully_qualified_name(type(data)))
            )
        if len(data.translations) == 1:
            with suppress(KeyError):
                # Explicitly cast to a string because pyyaml cannot dump ``str`` subclasses.
                return str(data.translations[None])
        return {
            # Explicitly cast to a string because pyyaml cannot dump ``str`` subclasses.
            to_language_tag(locale): str(translation)
            for locale, translation in data.translations.items()
        }


@final
class CountableLocalizableDefinition(DataDefinition[CountableLocalizable], Singleton):
    """
    The data definition for :py:class:`betty.localizable.CountableLocalizable`.
    """

    def __init__(self):
        super().__init__(
            cls=CountableLocalizable,
            label=_("A countable localizable string"),
            porter=_CountableLocalizablePorter(),
        )


class _CountableLocalizablePorter(Porter[CountableLocalizable]):
    load = override(
        assert_mapping(
            assert_mapping(
                assert_str(),
                assert_str(),
            ),
            assert_locale(),
        )
        | CountableStaticTranslations
    )

    @override
    def dump(self, data: CountableLocalizable) -> PortableData:
        if not isinstance(data, CountableStaticTranslations):
            raise NotDumpable(
                Plain(
                    "Only static translations and plain text can be dumped to portable data, not `{localizable}` objects."
                ).format(localizable=fully_qualified_name(type(data)))
            )
        return {
            to_language_tag(locale): translations
            for locale, translations in data.translations.items()
        }  # ty:ignore[invalid-return-type]
