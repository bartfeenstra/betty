"""
Provide Betty's ancestry genders.
"""

from __future__ import annotations

from typing import final

from betty.data import Data
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.data import DataPluginDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery
from betty.plugin.human_facing import CountableHumanFacingPluginDefinition


class Gender(Data, Plugin["GenderDefinition"]):
    """
    Define a gender.
    """


@final
@PluginTypeDefinition(
    "gender",
    base_cls=Gender,
    label=_("Gender"),
    label_plural=_("Genders"),
    label_countable=ngettext("{count} gender", "{count} genders"),
    discovery=[
        EntryPointDiscovery("betty.gender"),
        ProjectDiscovery(lambda project: project.configuration.genders.new_plugins()),
    ],
)
class GenderDefinition(
    CountableHumanFacingPluginDefinition[Gender], DataPluginDefinition[Gender]
):
    """
    .. plugin_type:: gender.

    From `gender <https://en.wikipedia.org/wiki/Gender>`_ on Wikipedia:

        Gender includes the social, psychological, cultural and behavioral aspects of being a man, woman, or other gender
        identity.
    """
