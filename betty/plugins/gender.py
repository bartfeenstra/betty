"""
Provide concrete gender implementations.
"""

from typing import final

from betty.classtools import Singleton
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


@final
@GenderDefinition(
    "unknown",
    label=_("Person of unknown gender"),
    label_plural=_("People of unknown gender"),
    label_countable=ngettext(
        "{count} person of unknown gender", "{count} people of unknown gender"
    ),
)
class Unknown(Gender, Singleton):
    """
    .. plugin:: gender:unknown.
    """


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
