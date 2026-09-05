from __future__ import annotations  # noqa: D100

import platform
import sys
from importlib import metadata
from typing import TYPE_CHECKING, Final, Self, final, override

from rich.table import Table

from betty import about
from betty.app import App
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.console.project import add_project_argument
from betty.definition.human_facing import HumanFacingDefinition
from betty.factory import Arg1Manufacturable
from betty.localizables.gettext import _
from betty.localizables.markup import Quote
from betty.rich.user import RichUser

if TYPE_CHECKING:
    import argparse
    from collections.abc import MutableSequence

    from betty.project import Project


@final
@CommandDefinition(
    "about", label=_("Output information about Betty, and optionally your project")
)
class About(Arg1Manufacturable[App], Command):
    """
    .. plugin:: command:about.
    """

    _key_style: Final[str] = "cyan"

    def __init__(self, app: App, /):
        self._app = app

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
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
            title=user.localizer.translate._("Your project at {path}").format(
                path=str(project.directory)
            ),
            show_header=False,
        )
        about_project.add_column("", style=self._key_style)
        about_project.add_column("")
        about_project.add_row(
            user.localizer.translate._("Asset directory"),
            str(project.asset_directory),
        )
        about_project.add_row(
            user.localizer.translate._("Output directory"),
            str(project.output_directory),
        )
        user.console.print(about_project, emoji=False, markup=False)

    async def _about_plugins(self, user: RichUser, project: Project | None) -> None:
        services = self._app if project is None else project
        about_plugins = Table(title=user.localizer.translate._("Plugins"))
        about_plugins.add_column(
            user.localizer.translate._("Type"), style=self._key_style
        )
        about_plugins.add_column(user.localizer.translate._("ID"))
        about_plugins.add_column(user.localizer.translate._("Label"))
        for plugin_manager in sorted(
            services.plugins,
            key=lambda plugin_type: plugin_type.type.type().label.localize(
                user.localizer
            ),
        ):
            for index, plugin in enumerate(
                sorted([x async for x in plugin_manager], key=lambda plugin: plugin.id)
            ):
                first_column = (
                    plugin_manager.type.type().label.localize(user.localizer)
                    if index == 0
                    else ""
                )
                third_column_lines: MutableSequence[str] = []
                if isinstance(plugin, HumanFacingDefinition):
                    third_column_lines.append(plugin.label.localize(user.localizer))
                about_plugins.add_row(
                    first_column,
                    plugin.id,
                    "\n".join(third_column_lines),
                )
        user.console.print(about_plugins, emoji=False, markup=False)
        if project is None:
            user.console.print(
                _(
                    "More plugins may be available when running this command with {argument}."
                )
                .format(argument=Quote("--project"))
                .localize(user.localizer),
                markup=False,
                style="yellow",
            )

    async def _about_system(self, user: RichUser) -> None:
        about_system = Table(
            title=user.localizer.translate._("System"), show_header=False
        )
        about_system.add_column("", style=self._key_style)
        about_system.add_column("")
        about_system.add_row("Betty", about.version_label)
        about_system.add_row(
            user.localizer.translate._("Operating system"), platform.platform()
        )
        about_system.add_row("Python", sys.version)
        user.console.print(about_system, emoji=False, markup=False)

    async def _about_python_packages(self, user: RichUser) -> None:
        about_python_packages = Table(
            title=user.localizer.translate._("Python packages")
        )
        about_python_packages.add_column(
            user.localizer.translate._("Package"), style=self._key_style
        )
        about_python_packages.add_column(user.localizer.translate._("Version"))
        for x in sorted(
            metadata.distributions(),
            key=lambda x: x.metadata["Name"].lower(),
        ):
            about_python_packages.add_row(x.metadata["Name"], x.version)
        user.console.print(about_python_packages, emoji=False, markup=False)
