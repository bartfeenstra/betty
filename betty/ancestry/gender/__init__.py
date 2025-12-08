"""
Provide Betty's ancestry genders.
"""

from __future__ import annotations

from typing import ClassVar, final

from betty.locale.localizable import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery
from betty.plugin.human_facing import CountableHumanFacingPluginDefinition


class Gender(Plugin):
    """
    Define a gender.

    Read more about :doc:`/development/plugin/gender`.
    """

    plugin: ClassVar[GenderPlugin]


@final
class GenderPlugin(CountableHumanFacingPluginDefinition[Gender]):
    """
    A gender definition.

    Read more about :doc:`/development/plugin/gender`.
    """

    plugin_type_cls = Gender
    type = PluginTypeDefinition(
        "gender",
        _("Gender"),
        _("Genders"),
        ngettext("{count} gender", "{count} genders"),
        discoveries=[
            EntryPointDiscovery("betty.gender"),
            ProjectDiscovery(
                lambda project: project.configuration.genders.new_plugins()
            ),
        ],
    )
