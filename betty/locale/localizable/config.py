"""
Provide localizable configuration.
"""

from contextlib import suppress

from betty.assertion import (
    assert_len,
    assert_locale_identifier,
    assert_mapping,
    assert_or,
    assert_str,
)
from betty.importlib import fully_qualified_name
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import Localizable, Plain, StaticTranslations, _
from betty.serde.dump import Dump, NotDumpable


def load_localizable(dump: Dump, /) -> Localizable:
    """
    Load a localizable from configuration.
    """
    translations = assert_or(
        assert_str().chain(lambda translation: {UNDETERMINED_LOCALE: translation}),
        assert_mapping(assert_str(), assert_locale_identifier()),
    )(dump)
    assert_len(minimum=1)(translations)
    return StaticTranslations(translations)


def dump_localizable(localizable: Localizable, /) -> Dump:
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
                return translations[UNDETERMINED_LOCALE]
        return dict(translations)
    raise NotDumpable(
        _(
            "Only plain text and static translations can be dumped to configuration, not `{localizable}` objects."
        ).format(localizable=fully_qualified_name(type(localizable)))
    )
