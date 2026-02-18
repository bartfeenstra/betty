"""Provide Betty's extension API."""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.definition.human_facing import HumanFacingDefinition
from betty.life_cycle.manage import ManagedLifeCycle
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition, ResolvableId
from betty.plugin.dependent import DependentPluginDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.factory import PluginManufacturer
from betty.service.level import ServiceLevel

if TYPE_CHECKING:
    import builtins
    from collections.abc import Set
    from pathlib import Path

    from betty.locale.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName


class Extension[ServiceLevelT: ServiceLevel](
    ManagedLifeCycle, Plugin["ExtensionDefinition"]
):
    """
    Integrate custom services with a :py:class:`service level <betty.service.level.ServiceLevel>`.
    """

    def __init__(self, *, services: ServiceLevelT):
        super().__init__()
        self._services = services

    @property
    def services(self) -> ServiceLevelT:
        """
        The service level this extension is attached to.
        """
        return self._services


@final
@PluginTypeDefinition(
    "extension",
    label=_("Extension"),
    label_plural=_("Extensions"),
    label_countable=ngettext("{count} extension", "{count} extensions"),
    discovery=[EntryPointDiscovery("betty.extension")],
)
class ExtensionDefinition(HumanFacingDefinition, DependentPluginDefinition[Extension]):
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
        comes_before: Set[ResolvableId] | None = None,
        comes_after: Set[ResolvableId] | None = None,
        depends_on: Set[ResolvableId] | None = None,
        assets_directory: Path | None = None,
        theme: bool = False,
    ):
        super().__init__(
            plugin_id,
            label=label,
            description=description,
            comes_before=comes_before,
            comes_after=comes_after,
            depends_on=depends_on,
        )
        self._assets_directory = assets_directory
        self._theme = theme

    @property
    def assets_directory(self) -> Path | None:
        """
        The path on disk where the extension's assets are located.
        """
        return self._assets_directory

    @property
    def theme(self) -> bool:
        """
        Whether this extension is a theme.
        """
        return self._theme


@final
class ExtensionManufacturer(PluginManufacturer[ExtensionDefinition, Extension]):
    """
    The extension manufacturer.
    """

    @override
    @classmethod
    def type(cls) -> builtins.type[ExtensionDefinition]:
        return ExtensionDefinition
