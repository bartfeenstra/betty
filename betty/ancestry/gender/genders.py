"""
Provide concrete gender implementations.
"""

from typing import final

from betty.ancestry.gender import Gender, GenderPlugin
from betty.classtools import Singleton
from betty.locale.localizable.gettext import _, ngettext


@final
@GenderPlugin(
    "man",
    label=_("Man"),
    label_plural=_("Men"),
    label_countable=ngettext("{count} man", "{count} men"),
)
class Man(Gender):
    """
    A man.
    """


@final
@GenderPlugin(
    "non-binary",
    label=_("Non-binary person"),
    label_plural=_("Non-binary people"),
    label_countable=ngettext("{count} non-binary person", "{count} non-binary people"),
)
class NonBinary(Gender):
    """
    A non-binary person.
    """


@final
@GenderPlugin(
    "unknown",
    label=_("Person of unknown gender"),
    label_plural=_("People of unknown gender"),
    label_countable=ngettext(
        "{count} person of unknown gender", "{count} people of unknown gender"
    ),
)
class Unknown(Gender, Singleton):
    """
    A person of an unknown gender.
    """


@final
@GenderPlugin(
    "woman",
    label=_("Woman"),
    label_plural=_("Women"),
    label_countable=ngettext("{count} woman", "{count} women"),
)
class Woman(Gender):
    """
    A woman.
    """
