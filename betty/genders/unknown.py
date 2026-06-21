"""
The unknown gender.
"""

from __future__ import annotations

from typing import final

from betty.classtools import Singleton
from betty.gender import Gender, GenderDefinition
from betty.localizables.gettext import _, ngettext


@final
@GenderDefinition(
    "unknown",
    label=_("Person of unknown gender"),
    label_plural=_("People of unknown gender"),
    label_countable=ngettext(
        "{count} person of unknown gender", "{count} people of unknown gender"
    ),
)
class UnknownGender(Gender, Singleton):
    """
    .. plugin:: gender:unknown.
    """
