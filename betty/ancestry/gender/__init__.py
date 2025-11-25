"""
Provide Betty's ancestry genders.
"""

from __future__ import annotations

from typing import ClassVar, final

from betty.locale.localizable import _
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery
from betty.plugin.human_facing import HumanFacingPluginDefinition


class Gender(Plugin):
    """
    Define a gender.

    Read more about :doc:`/development/plugin/gender`.
    """

    plugin: ClassVar[GenderDefinition]


@final
class GenderDefinition(HumanFacingPluginDefinition[Gender]):
    """
    A gender definition.

    Read more about :doc:`/development/plugin/gender`.
    """

    type = PluginTypeDefinition(
        "gender",
        Gender,
        _("Gender"),
        discoveries=[
            EntryPointDiscovery("betty.gender"),
            ProjectDiscovery(
                lambda project: project.configuration.genders.new_plugins()
            ),
        ],
    )
