"""Provide Betty's extension API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Generic, Self, TypeVar, final

from typing_extensions import override

from betty.config import Configuration, DefaultConfigurable
from betty.job import Context
from betty.locale.localizable import Join, Localizable, _
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    ClassedPluginTypeDefinition,
    CyclicDependencyError,
    DependentPluginDefinition,
    OrderedPluginDefinition,
    PluginIdMapping,
    PluginRepository,
    UserFacingPluginDefinition,
    resolve_identifier,
)
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.project.factory import ProjectDependentFactory
from betty.requirement import AllRequirements
from betty.service import ServiceProvider
from betty.typing import private

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from betty.project import Project
    from betty.requirement import Requirement
    from betty.user import User

_T = TypeVar("_T")
_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
_ContextT = TypeVar("_ContextT", bound=Context)


class Extension(ServiceProvider, ProjectDependentFactory, ClassedPlugin):
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
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project)

    @property
    def project(self) -> Project:
        """
        The project this extension runs within.
        """
        return self._project

    @classmethod
    async def requirement(cls, *, user: User) -> Requirement:
        """
        Define the requirement for this extension to be enabled.

        This defaults to the extension's dependencies.
        """
        return await Dependencies.new(cls.plugin, user=user)


_ExtensionT = TypeVar("_ExtensionT", bound=Extension)


@final
class ExtensionDefinition(
    UserFacingPluginDefinition,
    ClassedPluginDefinition[Extension],
    DependentPluginDefinition,
    OrderedPluginDefinition,
):
    """
    An extension definition.
    """

    type: ClassVar[ClassedPluginTypeDefinition] = ClassedPluginTypeDefinition(
        id="extension",
        label=_("Extension"),
        cls=Extension,
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


EXTENSION_REPOSITORY: PluginRepository[ExtensionDefinition] = (
    EntryPointPluginRepository(ExtensionDefinition, "betty.extension")
)

"""
The project extension plugin repository.

Read more about :doc:`/development/plugin/extension`.
"""


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


class Dependencies(AllRequirements):
    """
    Check a dependent's dependency requirements.
    """

    @private
    def __init__(
        self,
        dependent: ExtensionDefinition,
        extension_id_mapping: PluginIdMapping[ExtensionDefinition],
        dependency_requirements: Sequence[Requirement],
    ):
        super().__init__(*dependency_requirements)
        self._dependent = dependent
        self._extension_id_mapping = extension_id_mapping

    @classmethod
    async def new(cls, dependent: ExtensionDefinition, *, user: User) -> Self:
        """
        Create a new instance.
        """
        try:
            dependency_requirements = [
                await (
                    await EXTENSION_REPOSITORY.get(
                        resolve_identifier(dependency_identifier)
                    )
                ).cls.requirement(user=user)
                for dependency_identifier in dependent.depends_on
                & dependent.comes_after
            ]
        except RecursionError:
            raise CyclicDependencyError([dependent.id]) from None
        else:
            return cls(
                dependent, await EXTENSION_REPOSITORY.mapping(), dependency_requirements
            )

    @override
    def summary(self) -> Localizable:
        return _("{dependent_label} requires {dependency_labels}.").format(
            dependent_label=self._dependent.label,
            dependency_labels=Join(
                ", ",
                *(
                    self._extension_id_mapping[dependency_identifier].label
                    for dependency_identifier in self._dependent.depends_on
                ),
            ),
        )
