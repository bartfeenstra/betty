"""
Provide Betty's ancestry genders.
"""

from __future__ import annotations

from typing import final, override

from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.factory import PluginManufacturer


class Gender(Plugin["GenderDefinition"]):
    """
    Define a gender.
    """


@final
@PluginTypeDefinition(
    "gender",
    label=_("Gender"),
    label_plural=_("Genders"),
    label_countable=ngettext("{count} gender", "{count} genders"),
)
class GenderDefinition(CountableHumanFacingDefinition, PluginDefinition[Gender]):
    """
    .. plugin_type:: gender.

    From `gender <https://en.wikipedia.org/wiki/Gender>`_ on Wikipedia:

        Gender includes the social, psychological, cultural and behavioral aspects of being a man, woman, or other gender
        identity.
    """


@final
class GenderManufacturer(PluginManufacturer[GenderDefinition, Gender]):
    """
    The gender manufacturer.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[GenderDefinition]:
        return GenderDefinition
