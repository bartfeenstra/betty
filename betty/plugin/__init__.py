"""
The Plugin API.

Plugins allow third-party code (e.g. your own Python package) to add functionality
to Betty.
"""

from __future__ import annotations

from contextlib import suppress
from functools import update_wrapper
from typing import TYPE_CHECKING, Any, Never, Self, final, overload, override

from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.importlib import fully_qualified_name
from betty.machine_name import MachineName, ResolvableMachineName

if TYPE_CHECKING:
    import builtins
    from collections.abc import Iterable

    from betty.locale.localizable import CountableLocalizable, ResolvableLocalizable
    from betty.requirement import Requirement, ResolvableRequirement

if TYPE_CHECKING:
    type Requires = Iterable[ResolvableRequirement]
else:
    type Requires = Any


class PluginDefinition[BaseClsT](ClsDefinition[BaseClsT]):
    """
    A plugin definition.
    """

    def __init__(
        self, plugin_id: ResolvableMachineName, *, requires: Requires | None = None
    ):
        from betty.requirement import resolve_requirement

        super().__init__()
        self._id = MachineName.resolve(plugin_id)
        self._requires = (
            () if requires is None else tuple(map(resolve_requirement, requires))
        )

    @classmethod
    def type(cls) -> PluginTypeDefinition[BaseClsT, Self]:
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

    @override
    def _set_cls(self, cls: builtins.type[BaseClsT]) -> None:
        super()._set_cls(cls)
        cls.plugin = staticmethod(update_wrapper(lambda: self, cls.plugin))  # ty:ignore[unresolved-attribute]


@final
class PluginTypeDefinition[BaseClsT, PluginDefinitionT: PluginDefinition](
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
    def _set_cls(self, cls: type[PluginDefinitionT]) -> None:
        super()._set_cls(cls)
        cls.type = staticmethod(update_wrapper(lambda: self, cls.type))  # ty:ignore[invalid-assignment]


class Plugin[PluginDefinitionT: PluginDefinition]:
    """
    A plugin class.
    """

    @classmethod
    def plugin(cls) -> PluginDefinitionT:
        """
        The plugin definition.
        """
        raise NotImplementedError(
            f"{fully_qualified_name(cls)} was not decorated with a {fully_qualified_name(PluginDefinition)} subclass."
        )


type ResolvablePluginTypeDefinition = (
    PluginTypeDefinition | type[PluginDefinition] | ResolvablePluginDefinition
)


type ResolvablePluginTypeId = ResolvablePluginTypeDefinition | ResolvableMachineName
"""
Use :py:func:`betty.plugin.resolve_plugin_type_id` to resolve this to a plugin type ID.
"""


@overload
def resolve_plugin_type_id(plugin_type_id: ResolvablePluginTypeId, /) -> MachineName:
    pass


@overload
def resolve_plugin_type_id(plugin_type_id: Any, /) -> MachineName | Never:
    pass


def resolve_plugin_type_id(plugin_type_id):
    """
    Resolve a plugin type identifier to a plugin type ID.

    :raises ValueError: Raised if the value cannot be resolved to a plugin type ID.
    """
    if isinstance(plugin_type_id, PluginTypeDefinition):
        return plugin_type_id.id
    if isinstance(plugin_type_id, str):
        return MachineName.resolve(plugin_type_id)
    if isinstance(plugin_type_id, type) and issubclass(
        plugin_type_id, PluginDefinition
    ):
        return plugin_type_id.type().id
    with suppress(ValueError):
        return resolve_plugin_definition(plugin_type_id).type().id
    raise ValueError(f"'{plugin_type_id}' cannot be resolved to a plugin type ID.")


type ResolvablePluginDefinition[
    PluginDefinitionT: PluginDefinition = PluginDefinition
] = PluginDefinitionT | type[Plugin[PluginDefinitionT]]
"""
Use :py:func:`betty.plugin.resolve_plugin_definition` to resolve this to a :py:class:`betty.plugin.PluginDefinition`
"""


@overload
def resolve_plugin_definition[PluginDefinitionT: PluginDefinition](
    plugin_definition: ResolvablePluginDefinition[PluginDefinitionT], /
) -> PluginDefinitionT:
    pass


@overload
def resolve_plugin_definition[PluginDefinitionT: PluginDefinition](
    plugin_definition: ResolvablePluginDefinition[PluginDefinitionT] | Any, /
) -> PluginDefinitionT | Never:
    pass


def resolve_plugin_definition(plugin_definition):
    """
    Resolve a plugin definition.

    :raises ValueError: Raised if the value cannot be resolved to a plugin definition.
    """
    if isinstance(plugin_definition, PluginDefinition):
        return plugin_definition
    if isinstance(plugin_definition, type) and issubclass(plugin_definition, Plugin):
        return plugin_definition.plugin()
    raise ValueError(
        f"'{plugin_definition}' cannot be resolved to a plugin definition."
    )


type ResolvablePluginId[PluginDefinitionT: PluginDefinition = PluginDefinition] = (
    ResolvableMachineName | ResolvablePluginDefinition[PluginDefinitionT]
)
"""
Use :py:func:`betty.plugin.resolve_plugin_id` to resolve this to a plugin ID.
"""


@overload
def resolve_plugin_id(plugin_id: ResolvablePluginId, /) -> MachineName:
    pass


@overload
def resolve_plugin_id(plugin_id: Any, /) -> MachineName | Never:
    pass


def resolve_plugin_id(plugin_id):
    """
    Resolve a plugin identifier to a plugin ID.

    :raises ValueError: Raised if the value cannot be resolved to a plugin ID.
    """
    if isinstance(plugin_id, MachineName):
        return plugin_id
    if isinstance(plugin_id, str):
        return MachineName.resolve(plugin_id)
    with suppress(ValueError):
        return resolve_plugin_definition(plugin_id).id
    raise ValueError(f"'{plugin_id}' cannot be resolved to a plugin ID.") from None
