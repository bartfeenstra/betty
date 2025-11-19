"""
Provide Betty's ancestry genders.
"""

from __future__ import annotations

from typing import ClassVar, final

from betty.locale.localizable import _
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    HumanFacingPluginDefinition,
    PluginTypeDefinition,
)
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery


class Gender(ClassedPlugin):
    """
    Define a gender.

    Read more about :doc:`/development/plugin/gender`.
    """

    plugin: ClassVar[GenderDefinition]


@final
class GenderDefinition(HumanFacingPluginDefinition, ClassedPluginDefinition[Gender]):
    """
    A gender definition.

    Read more about :doc:`/development/plugin/gender`.
    """

    plugin_type_cls = Gender
    type = PluginTypeDefinition(
        id="gender",
        label=_("Gender"),
        discoveries=[
            EntryPointDiscovery("betty.gender"),
            ProjectDiscovery(
                lambda project: project.configuration.genders.new_plugins()
            ),
        ],
    )
