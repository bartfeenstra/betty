"""Provide Betty's extension API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Self, TypeVar, final

from typing_extensions import override

from betty.config import Configuration, DefaultConfigurable
from betty.locale.localizable import Localizable, _, call
from betty.plugin import (
    CyclicDependencyError,
    DependentPlugin,
    Plugin,
    PluginIdToTypeMapping,
    PluginRepository,
)
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.project.factory import ProjectDependentFactory
from betty.requirement import AllRequirements
from betty.service import ServiceProvider
from betty.typing import private

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from betty.event_dispatcher import EventHandlerRegistry
    from betty.machine_name import MachineName
    from betty.project import Project
    from betty.requirement import Requirement
    from betty.user import User

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class Extension(
    DependentPlugin["Extension"],
    ServiceProvider,
    ProjectDependentFactory,
):
    """
    Integrate optional functionality with Betty :py:class:`betty.project.Project`s.

    Read more about :doc:`/development/plugin/extension`.

    To test your own subclasses, use :py:class:`betty.test_utils.project.extension.ExtensionTestBase`.
    """

    def __init__(self, project: Project):
        assert type(self) is not Extension
        super().__init__()
        self._project = project

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project)

    @final
    @override
    @classmethod
    def plugin_type_cls(cls) -> type[Plugin]:
        return Extension

    @final
    @override
    @classmethod
    def plugin_type_id(cls) -> MachineName:
        return "extension"

    @final
    @override
    @classmethod
    def plugin_type_label(cls) -> Localizable:
        return _("Extension")

    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        """
        Register event handlers with the project.
        """

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
        return await Dependencies.new(cls, user=user)

    @classmethod
    def assets_directory_path(cls) -> Path | None:
        """
        Return the path on disk where the extension's assets are located.

        This may be anywhere in your Python package.
        """
        return None


_ExtensionT = TypeVar("_ExtensionT", bound=Extension)


EXTENSION_REPOSITORY: PluginRepository[Extension] = EntryPointPluginRepository(
    Extension, "betty.extension"
)
"""
The project extension plugin repository.

Read more about :doc:`/development/plugin/extension`.
"""


class Theme(Extension):
    """
    An extension that is a front-end theme.
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
        dependent: type[Extension],
        extension_id_to_type_mapping: PluginIdToTypeMapping[Extension],
        dependency_requirements: Sequence[Requirement],
    ):
        super().__init__(*dependency_requirements)
        self._dependent = dependent
        self._extension_id_to_type_mapping = extension_id_to_type_mapping

    @classmethod
    async def new(cls, dependent: type[Extension], *, user: User) -> Self:
        """
        Create a new instance.
        """
        try:
            dependency_requirements = [
                await (
                    await EXTENSION_REPOSITORY.get(dependency_identifier)
                    if isinstance(dependency_identifier, str)
                    else dependency_identifier
                ).requirement(user=user)
                for dependency_identifier in dependent.depends_on()
                & dependent.comes_after()
            ]
        except RecursionError:
            raise CyclicDependencyError([dependent]) from None
        else:
            return cls(
                dependent, await EXTENSION_REPOSITORY.mapping(), dependency_requirements
            )

    @override
    def summary(self) -> Localizable:
        return _("{dependent_label} requires {dependency_labels}.").format(
            dependent_label=self._dependent.plugin_label(),
            dependency_labels=call(
                lambda localizer: ", ".join(
                    self._extension_id_to_type_mapping[dependency_identifier]
                    .plugin_label()
                    .localize(localizer)
                    for dependency_identifier in self._dependent.depends_on()
                ),
            ),
        )
