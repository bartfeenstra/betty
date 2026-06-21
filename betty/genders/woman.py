"""
The woman gender.
"""

from __future__ import annotations

from typing import final

from betty.gender import Gender, GenderDefinition
from betty.localizables.gettext import _, ngettext


@final
@GenderDefinition(
    "woman",
    label=_("Woman"),
    label_plural=_("Women"),
    label_countable=ngettext("{count} woman", "{count} women"),
)
class Woman(Gender):
    """
    .. plugin:: gender:woman.
    """
