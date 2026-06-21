"""
The non-binary gender.
"""

from __future__ import annotations

from typing import final

from betty.gender import Gender, GenderDefinition
from betty.localizables.gettext import _, ngettext


@final
@GenderDefinition(
    "non-binary",
    label=_("Non-binary person"),
    label_plural=_("Non-binary people"),
    label_countable=ngettext("{count} non-binary person", "{count} non-binary people"),
)
class NonBinary(Gender):
    """
    .. plugin:: gender:non-binary.
    """
