"""
The Plugin API.

Plugins allow third-party code (e.g. your own Python package) to add functionality
to Betty.
"""

from __future__ import annotations

from functools import update_wrapper
from typing import TYPE_CHECKING, Any, Final, Never, Self, final, override

from betty.capability import Stage
from betty.definition import Definition
from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.importlib import fully_qualified_name
from betty.machine_name import MachineName, ResolvableMachineName

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.localizable import CountableLocalizable, ResolvableLocalizable
    from betty.requirement import Requirement, Requires


class PluginDefinition[StageT: Stage = Never](Definition[StageT]):
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

        super().__init__(*args, **kwargs)
        self.id: Final[MachineName] = MachineName.resolve(plugin_id)
        """
        The plugin ID.

        IDs are unique per plugin type:

        - A plugin repository **MUST** at most have a single plugin for any ID.
        - Different plugin repositories **MAY** each have a plugin with the same ID.
        """
        self.auto: Final[bool] = auto
        """
        Whether to enable this plugin automatically when its plugin type is used for a plugi. service.
        """
        self.requires: Final[Iterable[Requirement]] = tuple(requires)
        """
        The plugin's requirements.
        """

    @classmethod
    def type(cls) -> PluginTypeDefinition[Self]:
        """
        The plugin type definition.
        """
        raise NotImplementedError(
            f"{fully_qualified_name(cls)} was not decorated with a {fully_qualified_name(PluginDefinition)} subclass."
        )


@final
class PluginTypeDefinition[PluginDefinitionT: PluginDefinition](
    CountableHumanFacingDefinition, ClsDefinition[PluginDefinitionT]
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
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
        )

        self.id: Final[MachineName] = MachineName.resolve(plugin_type_id)
        """
        The plugin type ID.
        """

    @override
    def _set_cls(self, cls: type[PluginDefinitionT], /) -> None:
        super()._set_cls(cls)
        cls.type = staticmethod(  # ty:ignore[invalid-assignment]
            update_wrapper(
                lambda: self,  # ty:ignore[invalid-argument-type]
                cls.type,
            )
        )
