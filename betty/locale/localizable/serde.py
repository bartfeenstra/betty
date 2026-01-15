"""
(De)serialize localizables.
"""

from contextlib import suppress

from betty.assertion import assert_locale, assert_mapping, assert_or, assert_str
from betty.importlib import fully_qualified_name
from betty.locale import to_language_tag
from betty.locale.localizable import CountableLocalizable, Localizable
from betty.locale.localizable.gettext import _
from betty.locale.localizable.plain import Plain
from betty.locale.localizable.static import (
    CountableStaticTranslations,
    StaticTranslations,
)
from betty.portable import PortableData
from betty.portable.error import NotPortable


def load_localizable(portable: PortableData, /) -> Localizable:
    """
    Load a localizable from serialized data.
    """
    translations = assert_or(
        assert_str().chain(lambda translation: {None: translation}),
        assert_mapping(assert_str(), assert_locale()),
    )(portable)
    return StaticTranslations(translations)


def dump_localizable(localizable: Localizable, /) -> PortableData:
    """
    Dump a localizable.

    :raises betty.serde.dump.NotDumpable: Raised if the localizable was not dumpable.
    """
    if isinstance(localizable, Plain):
        localizable = StaticTranslations(
            {
                localizable.locale: localizable.text,
            }
        )
    if isinstance(localizable, StaticTranslations):
        translations = localizable.translations
        if len(translations) == 1:
            with suppress(KeyError):
                # Explicitly cast to a string because pyyaml cannot dump ``str`` subclasses.
                return str(translations[None])
        return {
            # Explicitly cast to a string because pyyaml cannot dump ``str`` subclasses.
            to_language_tag(locale): str(translation)
            for locale, translation in translations.items()
        }
    raise NotPortable(
        _(
            "Only plain text and static translations can be dumped to serialized data, not `{localizable}` objects."
        ).format(localizable=fully_qualified_name(type(localizable)))
    )


def load_countable_localizable(portable: PortableData, /) -> CountableLocalizable:
    """
    Load a countable localizable from serialized data.
    """
    return CountableStaticTranslations(
        assert_mapping(
            assert_mapping(
                assert_str(),
                assert_str(),
            ),
            assert_locale(),
        )(portable)
    )


def dump_countable_localizable(localizable: CountableLocalizable, /) -> PortableData:
    """
    Dump a countable localizable.

    :raises betty.serde.dump.NotDumpable: Raised if the localizable was not dumpable.
    """
    if isinstance(localizable, CountableStaticTranslations):
        return {
            to_language_tag(locale): translations  # type: ignore[misc]
            for locale, translations in localizable.translations.items()
        }
    raise NotPortable(
        _(
            "Only countable static translations can be dumped to serialized data, not `{localizable}` objects."
        ).format(localizable=fully_qualified_name(type(localizable)))
    )
