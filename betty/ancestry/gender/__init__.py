"""
Provide Betty's ancestry genders.
"""

from __future__ import annotations

from typing import ClassVar, final

from betty.locale.localizable import _
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    ClassedPluginTypeDefinition,
    HumanFacingPluginDefinition,
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

    type: ClassVar[ClassedPluginTypeDefinition] = ClassedPluginTypeDefinition(
        id="gender",
        label=_("Gender"),
        cls=Gender,
    )
