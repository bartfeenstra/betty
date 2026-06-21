"""
Linked data for the localizable API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.locale import to_language_tag
from betty.locale.localizable.static import StaticTranslations

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.locale.localizable import Localizable
    from betty.locale.localize import Localizer
    from betty.portable import PortableMapping


def dump_linked_data(
    localizable: Localizable, *, localizers: Iterable[Localizer]
) -> PortableMapping:
    """
    Dump a :py:class:`betty.locale.localizable.Localizable` to `JSON-LD <https://json-ld.org/>`_.
    """
    return {
        to_language_tag(locale): translation
        for locale, translation in StaticTranslations.resolve(
            localizable, localizers
        ).translations.items()
    }
