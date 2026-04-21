"""Provide Betty's extension API."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Final, Protocol, Self, final, overload, override

from betty.classtools import Singleton
from betty.definition.human_facing import HumanFacingDefinition
from betty.life_cycle.manage import ManagedLifeCycle
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer
from betty.service.plugin import PluginServiceProvider
from betty.service.plugin.instance.collection import (
    CollectionPluginInstanceServiceManager as CollectionPluginInstanceServiceManager,
)
from betty.service.plugin.instance.collection.keyed import PluginInstancesService

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.plugin import Requires
    from betty.plugin.resolve import ResolvablePluginDefinition
    from betty.requirement import Requirement
    from betty.typing import Intersection


class Extension(ManagedLifeCycle, Plugin["ExtensionDefinition"]):
    """
    Integrate custom services with a :py:class:`service level <betty.service_level.ServiceLevel>`.
    """


@final
@PluginTypeDefinition(
    "extension",
    label=_("Extension"),
    label_plural=_("Extensions"),
    label_countable=ngettext("{count} extension", "{count} extensions"),
)
class ExtensionDefinition(HumanFacingDefinition, PluginClsDefinition[Extension]):
    """
    .. plugin_type:: extension.

    Betty's functionality can be altered using *extensions*. An extension can do many things, such as loading new or
    expanding existing ancestry data, or generating additional content for your site.

    Some extensions are configurable. That means that other than enabling them, you can set the configuration options
    that determine how the extension should work. This can be done in your project's
    :py:class:`configuration <betty.project.data.ProjectConfiguration>`.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id, label=label, description=description, requires=requires
        )


@final
class ExtensionManufacturer(PluginManufacturer[ExtensionDefinition, Extension]):
    """
    The extension manufacturer.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[ExtensionDefinition]:
        return ExtensionDefinition


class _ExtensionsServiceRequirementPlugins(Protocol):
    def __call__(
        self, *plugins: ResolvablePluginDefinition[ExtensionDefinition]
    ) -> Requirement:
        raise NotImplementedError


@final
class _ExtensionsServiceRequirementGetter(Singleton):
    @overload
    def __get__(self, instance: None, owner: type[ExtensionsService]) -> Self:
        pass

    @overload
    def __get__(
        self,
        instance: ExtensionsService,
        owner: type[ExtensionsService] | None = None,
    ) -> _ExtensionsServiceRequirementPlugins:
        pass

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return partial(self._require, instance)

    def _require(
        self,
        service: ExtensionsService,
        *plugins: ResolvablePluginDefinition[ExtensionDefinition],
    ) -> Requirement:
        raise NotImplementedError


@final
class ExtensionsService[
    ServiceProviderT: Intersection[PluginServiceProvider, Extension],
    PluginDefinitionT: PluginClsDefinition,
    PluginT: Plugin,
](PluginInstancesService[ServiceProviderT, PluginDefinitionT, PluginT]):
    """
    A service of extensions keyed by their IDs.
    """

    require: Final[_ExtensionsServiceRequirementGetter] = (
        _ExtensionsServiceRequirementGetter()
    )

    def __init__(self):
        super().__init__(ExtensionDefinition)
