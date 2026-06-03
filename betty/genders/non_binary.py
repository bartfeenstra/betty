"""
The non-binary gender.
"""

from typing import final

from betty.gender import Gender, GenderDefinition
from betty.locale.localizable.gettext import _, ngettext


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
