"""
The Plugin API.

Plugins allow third-party code (e.g. your own Python package) to add functionality
to Betty.
"""

from __future__ import annotations

from functools import update_wrapper
from typing import TYPE_CHECKING, Self, final, override

from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.importlib import fully_qualified_name
from betty.machine_name import MachineName, ResolvableMachineName

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.locale.localizable import CountableLocalizable, ResolvableLocalizable
    from betty.requirement import Requirement, Requires


class PluginDefinition:
    """
    A plugin definition.
    """

    def __init__(self, plugin_id: ResolvableMachineName, *, requires: Requires = ()):
        from betty.requirement import resolve_requirement

        super().__init__()
        self._id = MachineName.resolve(plugin_id)
        self._requires = tuple(map(resolve_requirement, requires))

    @classmethod
    def type(cls) -> PluginTypeDefinition[Self]:
        """
        The plugin type definition.
        """
        raise NotImplementedError(
            f"{fully_qualified_name(cls)} was not decorated with a {fully_qualified_name(PluginDefinition)} subclass."
        )

    @property
    def id(self) -> MachineName:
        """
        The plugin ID.

        IDs are unique per plugin type:

        - A plugin repository **MUST** at most have a single plugin for any ID.
        - Different plugin repositories **MAY** each have a plugin with the same ID.
        """
        return self._id

    @property
    def requires(self) -> Iterable[Requirement]:
        """
        The plugin's requirements.
        """
        return self._requires


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

        self._id = MachineName.resolve(plugin_type_id)

    @property
    def id(self) -> MachineName:
        """
        The plugin type ID.
        """
        return self._id

    @override
    def _set_cls(self, cls: type[PluginDefinitionT], /) -> None:
        super()._set_cls(cls)
        cls.type = staticmethod(update_wrapper(lambda: self, cls.type))  # ty:ignore[invalid-assignment]
