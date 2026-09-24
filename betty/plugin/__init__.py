"""
The Plugin API.

Plugins allow third-party code (e.g. your own Python package) to add functionality
to Betty.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, final

from betty.definition import HasDefinition
from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.definition.id import IdentifiableDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.localizable import CountableLocalizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requirement, Requires


class PluginDefinition(IdentifiableDefinition, HasDefinition["PluginTypeDefinition"]):
    """
    A plugin definition.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *args: Any,
        auto: bool = False,
        requires: Requires = (),
        **kwargs: Any,
    ):

        super().__init__(*args, id=plugin_id, **kwargs)
        self.auto: Final[bool] = auto
        """
        Whether to enable this plugin automatically when its plugin type is used for a plugi. service.
        """
        self.requires: Final[Iterable[Requirement]] = tuple(requires)
        """
        The plugin's requirements.
        """


@final
class PluginTypeDefinition[DefinitionT: PluginDefinition](
    CountableHumanFacingDefinition, ClsDefinition[DefinitionT], IdentifiableDefinition
):
    """
    A plugin type definition.
    """

    def __init__(
        self,
        plugin_type_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        label_plural: ResolvableLocalizable,
        label_countable: CountableLocalizable,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            id=plugin_type_id,
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
        )
