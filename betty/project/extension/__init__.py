"""Provide Betty's extension API."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Self, TypeVar, final

from typing_extensions import override

from betty.locale.localizable import LocalizableLike, _
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.dependent import DependentPluginDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.human_facing import HumanFacingPluginDefinition
from betty.plugin.requirement import new_dependencies_requirement
from betty.requirement import HasRequirement, Requirement, StaticRequirement
from betty.service.container import ServiceContainer

if TYPE_CHECKING:
    from collections.abc import Set
    from pathlib import Path

    from betty.machine_name import MachineName
    from betty.plugin.resolve import ResolvableId
    from betty.service.level import ServiceLevel


class Extension(ServiceContainer, Plugin, HasRequirement):
    """
    Integrate optional functionality with Betty :py:class:`betty.project.Project`s.

    Read more about :doc:`/development/plugin/extension`.

    To test your own subclasses, use :py:class:`betty.test_utils.project.extension.ExtensionTestBase`.
    """

    plugin: ClassVar[ExtensionPlugin]

    @override
    @classmethod
    async def requires(
        cls, services: ServiceLevel, subject: LocalizableLike, /
    ) -> Requirement | Self:
        from betty.project import Project

        project = await Project.requires(services, subject)
        if isinstance(project, Requirement):
            return project

        extensions = await project.extensions
        if cls.plugin.id not in extensions:
            return StaticRequirement(
                _(
                    "{subject} requires the {extension} extension. Enable it in your project configuration, and try again."
                ).format(subject=subject, extension=cls.plugin.reference_label)
            )
        return extensions[cls]

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        from betty.project import Project

        project = await Project.requires(services, cls.plugin.reference_label_with_type)
        if isinstance(project, Requirement):
            return project
        return await new_dependencies_requirement(
            cls.plugin,
            await project.plugins(ExtensionPlugin, check_requirements=False),
            services=project,
        )


_ExtensionT = TypeVar("_ExtensionT", bound=Extension)


@final
class ExtensionPlugin(
    HumanFacingPluginDefinition[Extension], DependentPluginDefinition[Extension]
):
    """
    An extension definition.
    """

    plugin_type_cls = Extension
    type = PluginTypeDefinition(
        "extension",
        _("Extension"),
        discoveries=EntryPointDiscovery("betty.extension"),
    )

    def __init__(
        self,
        plugin_id: MachineName,
        *,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
        comes_before: Set[ResolvableId] | None = None,
        comes_after: Set[ResolvableId] | None = None,
        depends_on: Set[ResolvableId] | None = None,
        assets_directory_path: Path | None = None,
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
        self._assets_directory_path = assets_directory_path
        self._theme = theme

    @property
    def assets_directory_path(self) -> Path | None:
        """
        The path on disk where the extension's assets are located.
        """
        return self._assets_directory_path

    @property
    def theme(self) -> bool:
        """
        Whether this extension is a theme.
        """
        return self._theme
