"""Provide Betty's extension API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Generic, Self, TypeVar, final

from typing_extensions import override

from betty.config import Configuration, DefaultConfigurable
from betty.job import Context
from betty.locale.localizable import Localizable, _
from betty.plugin import PluginTypeDefinition
from betty.plugin.classed import ClassedPlugin, ClassedPluginDefinition
from betty.plugin.dependent import DependentPluginDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.human_facing import HumanFacingPluginDefinition
from betty.plugin.ordered import OrderedPluginDefinition
from betty.plugin.requirement import new_dependencies_requirement
from betty.project.factory import ProjectDependentFactory
from betty.requirement import Requirement, StaticRequirement
from betty.service.container import ServiceContainer

if TYPE_CHECKING:
    from pathlib import Path

    from betty.project import Project
    from betty.service.level import ServiceLevel

_T = TypeVar("_T")
_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
_ContextT = TypeVar("_ContextT", bound=Context)


class Extension(ServiceContainer, ProjectDependentFactory, ClassedPlugin):
    """
    Integrate optional functionality with Betty :py:class:`betty.project.Project`s.

    Read more about :doc:`/development/plugin/extension`.

    To test your own subclasses, use :py:class:`betty.test_utils.project.extension.ExtensionTestBase`.
    """

    plugin: ClassVar[ExtensionDefinition]

    def __init__(self, project: Project):
        assert type(self) is not Extension
        super().__init__()
        self._project = project

    @override
    @classmethod
    async def requires(
        cls, services: ServiceLevel, subject: Localizable | str, /
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
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project)

    @property
    def project(self) -> Project:
        """
        The project this extension runs within.
        """
        return self._project

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        from betty.project import Project

        project = await Project.requires(services, cls.plugin.reference_label_with_type)
        if isinstance(project, Requirement):
            return project
        return await new_dependencies_requirement(
            cls.plugin,
            await project.plugins(ExtensionDefinition, check_requirements=False),
            services=project,
        )


_ExtensionT = TypeVar("_ExtensionT", bound=Extension)


@final
class ExtensionDefinition(
    HumanFacingPluginDefinition,
    ClassedPluginDefinition[Extension],
    DependentPluginDefinition,
    OrderedPluginDefinition,
):
    """
    An extension definition.
    """

    plugin_type_cls = Extension
    type = PluginTypeDefinition(
        id="extension",
        label=_("Extension"),
        discoveries=EntryPointDiscovery("betty.extension"),
    )

    def __init__(
        self,
        *,
        assets_directory_path: Path | None = None,
        theme: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
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


class ConfigurableExtension(
    DefaultConfigurable[_ConfigurationT], Extension, Generic[_ConfigurationT]
):
    """
    A configurable extension.
    """

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project, configuration=cls.new_default_configuration())
