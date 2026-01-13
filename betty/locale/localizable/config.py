"""
Provide localizable configuration.
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
from betty.serde import NotDumpable, SerializedData


def load_localizable(serialized: SerializedData, /) -> Localizable:
    """
    Load a localizable from configuration.
    """
    translations = assert_or(
        assert_str().chain(lambda translation: {None: translation}),
        assert_mapping(assert_str(), assert_locale()),
    )(serialized)
    return StaticTranslations(translations)


def dump_localizable(localizable: Localizable, /) -> SerializedData:
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
    raise NotDumpable(
        _(
            "Only plain text and static translations can be dumped to configuration, not `{localizable}` objects."
        ).format(localizable=fully_qualified_name(type(localizable)))
    )


def load_countable_localizable(serialized: SerializedData, /) -> CountableLocalizable:
    """
    Load a countable localizable from configuration.
    """
    return CountableStaticTranslations(
        assert_mapping(
            assert_mapping(
                assert_str(),
                assert_str(),
            ),
            assert_locale(),
        )(serialized)
    )


def dump_countable_localizable(localizable: CountableLocalizable, /) -> SerializedData:
    """
    Dump a countable localizable.

    :raises betty.serde.dump.NotDumpable: Raised if the localizable was not dumpable.
    """
    if isinstance(localizable, CountableStaticTranslations):
        return {
            to_language_tag(locale): translations  # type: ignore[misc]
            for locale, translations in localizable.translations.items()
        }
    raise NotDumpable(
        _(
            "Only countable static translations can be dumped to configuration, not `{localizable}` objects."
        ).format(localizable=fully_qualified_name(type(localizable)))
    )
