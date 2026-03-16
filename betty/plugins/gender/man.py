"""
The man gender.
"""

from typing import final

from betty.gender import Gender, GenderDefinition
from betty.locale.localizable.gettext import _, ngettext


@final
@GenderDefinition(
    "man",
    label=_("Man"),
    label_plural=_("Men"),
    label_countable=ngettext("{count} man", "{count} men"),
)
class Man(Gender):
    """
    .. plugin:: gender:man.
    """
