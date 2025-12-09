from __future__ import annotations  # noqa D100

import platform
import sys
from importlib import metadata
from typing import TYPE_CHECKING, final, Self

from rich.table import Table
from typing_extensions import override

from betty import about
from betty.app.factory import AppDependentSelfFactory
from betty.console.command import Command, CommandFunction, CommandDefinition
from betty.console.project import add_project_argument
from betty.rich.user import RichUser
from betty.locale.localizable.gettext import _
from betty.plugin import plugin_types
from betty.plugin.human_facing import HumanFacingPluginDefinition
from betty.plugin.requirement import get_requirement

if TYPE_CHECKING:
    import argparse
    from collections.abc import MutableSequence

    from betty.app import App
    from betty.project import Project


@final
@CommandDefinition(
    "about", label=_("Output information about Betty, and optionally your project")
)
class About(AppDependentSelfFactory, Command):
    """
    A command to generate a new site.
    """

    _KEY_STYLE = "cyan"

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App, /) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        return await add_project_argument(
            parser, self._command_function, self._app, required=False
        )

    async def _command_function(self, project: Project | None) -> None:
        user = self._app.user
        assert isinstance(user, RichUser)
        try:
            if project:
                await project.bootstrap()
                await self._about_project(user, project)
            await self._about_plugins(user, project)
            await self._about_python_packages(user)
            await self._about_system(user)
        finally:
            if project:
                await project.shutdown()

    async def _about_project(self, user: RichUser, project: Project) -> None:
        about_project = Table(
            title=user.localizer._("Your project at {file}").format(
                file=str(project.configuration_file_path.parent)
            ),
            show_header=False,
        )
        about_project.add_column("", style=self._KEY_STYLE)
        about_project.add_column("")
        about_project.add_row(
            user.localizer._("Configuration file"),
            str(project.configuration_file_path),
        )
        about_project.add_row(
            user.localizer._("Assets directory"),
            str(project.assets_directory_path),
        )
        about_project.add_row(
            user.localizer._("Output directory"),
            str(project.output_directory_path),
        )
        user.console.print(about_project)

    async def _about_plugins(self, user: RichUser, project: Project | None) -> None:
        services = self._app if project is None else project
        about_plugins = Table(title=user.localizer._("Plugins"))
        about_plugins.add_column(user.localizer._("Type"), style=self._KEY_STYLE)
        about_plugins.add_column(user.localizer._("ID"))
        about_plugins.add_column(user.localizer._("Label"))
        for plugin_type in sorted(
            plugin_types().values(),
            key=lambda plugin_type: plugin_type.type().label.localize(user.localizer),
        ):
            repository = await services.plugins(plugin_type, check_requirements=False)
            for index, plugin in enumerate(
                sorted(repository, key=lambda plugin: plugin.id)
            ):
                first_column = (
                    plugin_type.type().label.localize(user.localizer)
                    if index == 0
                    else ""
                )
                third_column_lines: MutableSequence[str] = []
                if isinstance(plugin, HumanFacingPluginDefinition):
                    third_column_lines.append(plugin.label.localize(user.localizer))
                requirement = await get_requirement(plugin, services)
                if requirement:
                    third_column_lines.append(
                        "[yellow]" + requirement.localize(user.localizer)
                    )
                about_plugins.add_row(
                    first_column,
                    plugin.id,
                    "\n".join(third_column_lines),
                )
        user.console.print(about_plugins)
        if project is None:
            user.console.print(
                "[yellow]"
                + user.localizer._(
                    "More plugins may be available when running this command with --project."
                )
            )

    async def _about_system(self, user: RichUser) -> None:
        about_system = Table(title=user.localizer._("System"), show_header=False)
        about_system.add_column("", style=self._KEY_STYLE)
        about_system.add_column("")
        about_system.add_row("Betty", about.VERSION_LABEL)
        about_system.add_row(user.localizer._("Operating system"), platform.platform())
        about_system.add_row("Python", sys.version)
        user.console.print(about_system)

    async def _about_python_packages(self, user: RichUser) -> None:
        about_python_packages = Table(title=user.localizer._("Python packages"))
        about_python_packages.add_column(
            user.localizer._("Package"), style=self._KEY_STYLE
        )
        about_python_packages.add_column(user.localizer._("Version"))
        for x in sorted(
            metadata.distributions(),
            key=lambda x: x.metadata["Name"].lower(),  # type: ignore[no-any-return, unused-ignore]
        ):
            about_python_packages.add_row(x.metadata["Name"], x.version)
        user.console.print(about_python_packages)
