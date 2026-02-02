"""Provide Betty's extension API."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, final

from typing_extensions import override

from betty.definition.human_facing import HumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition, ResolvableId
from betty.plugin.dependent import DependentPluginDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.service.container import ServiceContainer
from betty.typing import Void, private

if TYPE_CHECKING:
    from collections.abc import Set
    from pathlib import Path

    from betty.data import Data
    from betty.locale.localizable import ResolvableLocalizable
    from betty.machine_name import MachineName
    from betty.portable import PortableData
    from betty.project import Project
    from betty.service.level.factory import ServiceLevelTarget


_T = TypeVar("_T")


class Extension(ServiceContainer, Plugin["ExtensionDefinition"]):
    """
    Integrate optional functionality with Betty :py:class:`projects <betty.project.Project>`.
    """

    @private
    def __init__(self, *, project: Project):
        super().__init__()
        self._project = project

    @override
    async def _new_target(
        self,
        target: ServiceLevelTarget[_T],
        configuration: Data | PortableData | Void = Void(),  # noqa: B008
        /,
    ) -> _T:
        return await self._project.new_target(target, configuration)


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
    :py:class:`configuration <betty.project.config.ProjectConfiguration>`.
    """

    def __init__(
        self,
        plugin_id: MachineName,
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
