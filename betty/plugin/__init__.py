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
from betty.discoverers.entry_point import EntryPointDiscoverer
from betty.string import kebab_case_to_snake_case

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.definition.discover import Discovery
    from betty.localizable import CountableLocalizable
    from betty.localizer import AnyLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requirement, Requires


class PluginDefinition(IdentifiableDefinition, HasDefinition["PluginTypeDefinition"]):
    """
    A plugin definition.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        /,
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
        id_: ResolvableMachineName,
        /,
        *,
        label: AnyLocalizable,
        label_plural: AnyLocalizable,
        label_countable: CountableLocalizable,
        description: AnyLocalizable | None = None,
        discovery: Discovery[DefinitionT] | None = None,
    ):
        super().__init__(
            id=id_,
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
        )
        self._discovery = discovery

    @property
    def discovery(self) -> Discovery[DefinitionT]:
        """
        The discovery for plugins of this type.
        """
        return self._discovery or EntryPointDiscoverer(
            self.cls, kebab_case_to_snake_case(self.id)
        )
