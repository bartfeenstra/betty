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
    ProjectPluginRepositoryDefinition,
)


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
        repository=ProjectPluginRepositoryDefinition(
            lambda project: project.gender_repository
        ),
    )
