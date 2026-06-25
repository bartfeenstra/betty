"""
Linked data for the localizable API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.linked_data import LinkedData
from betty.locale import to_language_tag
from betty.localizables.static import StaticTranslations

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.localizable import Localizable
    from betty.localizer import Localizer


def dump_linked_data(
    localizable: Localizable, *, localizers: Iterable[Localizer]
) -> LinkedData:
    """
    Dump a :py:class:`betty.localizable.Localizable` to `JSON-LD <https://json-ld.org/>`_.
    """
    return LinkedData({
        to_language_tag(locale): translation
        for locale, translation in StaticTranslations.resolve(
            localizable, localizers
        ).translations.items()
    })
