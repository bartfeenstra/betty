"""
Linked data for the localizable API.
"""

from collections.abc import Iterable

from betty.locale import to_language_tag
from betty.locale.localizable import Localizable
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localize import Localizer
from betty.serde.dump import Dump, DumpMapping


def dump_linked_data(
    localizable: Localizable, *, localizers: Iterable[Localizer]
) -> DumpMapping[Dump]:
    """
    Dump a :py:class:`betty.locale.localizable.Localizable` to `JSON-LD <https://json-ld.org/>`_.
    """
    return {
        to_language_tag(locale): translation
        for locale, translation in StaticTranslations.from_localizable(
            localizable, localizers
        ).translations.items()
    }
