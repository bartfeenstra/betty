"""
The Plugin API.

Plugins allow third-party code (e.g. your own Python package) to add functionality
to Betty.
"""

from __future__ import annotations

from functools import update_wrapper
from typing import TYPE_CHECKING, Generic, Self, TypeAlias, final, overload

from typing_extensions import TypeVar, override

from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import CountableHumanFacingDefinition
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.machine_name import InvalidMachineName, MachineName, validate_machine_name
from betty.service.level import universe

if TYPE_CHECKING:
    import builtins
    from collections.abc import Iterable

    from ty_extensions import Intersection

    from betty.locale.localizable import (
        CountableLocalizable,
        Localizable,
        ResolvableLocalizable,
    )
    from betty.plugin.discovery import Discoverer, ResolvableDiscovery

_BaseClsCoT = TypeVar("_BaseClsCoT", default=object, covariant=True)


class PluginDefinition(ClsDefinition[_BaseClsCoT], Generic[_BaseClsCoT]):
    """
    A plugin definition.
    """

    def __init__(self, plugin_id: MachineName, /):
        super().__init__()
        if not validate_machine_name(plugin_id):
            raise InvalidMachineName(plugin_id)
        self._id = plugin_id

    @classmethod
    def type(cls) -> PluginTypeDefinition[_BaseClsCoT, Self]:
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

    @override
    def _set_cls(self, cls: builtins.type[_BaseClsCoT]) -> None:
        super()._set_cls(cls)
        cls.plugin = staticmethod(update_wrapper(lambda: self, cls.plugin))  # ty:ignore[unresolved-attribute]

    @property
    def reference_label(self) -> Localizable:
        """
        The label to reference this plugin with.
        """
        return _('"{plugin_id}"').format(plugin_id=self.id)

    @property
    def reference_label_with_type(self) -> Localizable:
        """
        The label to reference this plugin with, including the plugin type.
        """
        return _('{plugin_type} "{plugin_id}"').format(
            plugin_type=self.type().label,
            plugin_id=self.id,
        )


_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)
_PluginDefinitionCoT = TypeVar(
    "_PluginDefinitionCoT",
    bound=PluginDefinition,
    default=PluginDefinition,
    covariant=True,
)


@final
class PluginTypeDefinition(
    CountableHumanFacingDefinition,
    ClsDefinition[_PluginDefinitionCoT],
    Generic[_BaseClsCoT, _PluginDefinitionCoT],
):
    """
    A plugin type definition.
    """

    def __init__(
        self,
        id: MachineName,  # noqa: A002
        *,
        label: ResolvableLocalizable,
        label_plural: ResolvableLocalizable,
        label_countable: CountableLocalizable,
        description: ResolvableLocalizable | None = None,
        discovery: Iterable[ResolvableDiscovery[_PluginDefinitionCoT]] | None = None,
    ):
        from betty.plugin.discovery import Discoverer

        super().__init__(
            label=label,
            label_plural=label_plural,
            label_countable=label_countable,
            description=description,
        )

        if not validate_machine_name(id):
            raise InvalidMachineName(id)
        self._id = id
        self._discoverer = Discoverer[_PluginDefinitionCoT](discovery)

    @property
    def id(self) -> MachineName:
        """
        The plugin type ID.
        """
        return self._id

    @override
    def _set_cls(self, cls: type[_PluginDefinitionCoT]) -> None:
        super()._set_cls(cls)
        cls.type = staticmethod(update_wrapper(lambda: self, cls.type))  # ty:ignore[invalid-assignment]

    @property
    def discoverer(
        self,
    ) -> Discoverer[_PluginDefinitionCoT]:
        """
        The plugin discoverer for this type.
        """
        return self._discoverer


_PluginTypeDefinitionT = TypeVar("_PluginTypeDefinitionT", bound=PluginTypeDefinition)


class Plugin(Generic[_PluginDefinitionCoT]):
    """
    A plugin class.

    ``__init__()`` is considered private to the :py:mod:`factory <betty.factory>` API. That means you MUST use the
    factory API to create new instances.
    """

    @classmethod
    def plugin(cls) -> _PluginDefinitionCoT:
        """
        The plugin definition.
        """
        raise NotImplementedError(
            f"{fully_qualified_name(cls)} was not decorated with a {fully_qualified_name(PluginDefinition)} subclass."
        )


_PluginT = TypeVar("_PluginT", bound=Plugin)

ResolvableDefinition: TypeAlias = _PluginDefinitionT | type[Plugin[_PluginDefinitionT]]
"""
Use :py:func:`betty.plugin.resolve_definition` to resolve this to a :py:class:`betty.plugin.PluginDefinition`
"""


ResolvableId: TypeAlias = MachineName | ResolvableDefinition[_PluginDefinitionT]
"""
Use :py:func:`betty.plugin.resolve_id` to resolve this to a plugin ID.
"""


@overload
def resolve_type_definition(
    definition: _PluginTypeDefinitionT,
    /,
) -> _PluginTypeDefinitionT:
    pass


@overload
def resolve_type_definition(
    definition: type[
        Intersection[
            _PluginDefinitionT,
            PluginDefinition[Plugin[_PluginDefinitionT]],
            PluginDefinition[_PluginT],
        ]
    ],
    /,
) -> PluginTypeDefinition[
    Intersection[Plugin[_PluginDefinitionT], _PluginT], _PluginDefinitionT
]:
    pass


@overload
def resolve_type_definition(
    definition: MachineName,
    /,
) -> PluginTypeDefinition:
    pass


def resolve_type_definition(definition):
    """
    Resolve a plugin type definition.
    """
    if isinstance(definition, PluginTypeDefinition):
        return definition
    if isinstance(definition, str):
        return universe.plugins.types[definition]
    return definition.type()


def resolve_definition(
    definition: ResolvableDefinition[_PluginDefinitionT], /
) -> _PluginDefinitionT:
    """
    Resolve a plugin definition.
    """
    if isinstance(definition, PluginDefinition):
        return definition  # ty:ignore[invalid-return-type]
    return definition.plugin()


def resolve_id(plugin_id: ResolvableId, /) -> MachineName:
    """
    Resolve a plugin identifier to a plugin ID.
    """
    if isinstance(plugin_id, str):
        return plugin_id
    return resolve_definition(plugin_id).id
