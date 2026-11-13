"""
The man gender.
"""

from __future__ import annotations

from typing import final

from betty.freezers.classtools import FrozenOnInit
from betty.gender import Gender, GenderDefinition
from betty.localizables.gettext import _, ngettext


@final
@GenderDefinition(
    "man",
    label=_("Man"),
    label_plural=_("Men"),
    label_countable=ngettext("{count} man", "{count} men"),
)
class Man(Gender, FrozenOnInit):
    """
    .. plugin:: gender:man.
    """
