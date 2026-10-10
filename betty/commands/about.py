from __future__ import annotations  # noqa: D100

import platform
import sys
from importlib import metadata
from typing import TYPE_CHECKING, Final, Self, final, override

from rich.table import Table

from betty import about
from betty.app import App
from betty.console import Command, CommandDefinition
from betty.console.project import add_project_argument
from betty.definition.human_facing import HumanFacingDefinition
from betty.factory import Manufacturable
from betty.localizables.gettext import _
from betty.localizables.markup import Quote
from betty.uis.console import Console

if TYPE_CHECKING:
    import argparse
    from collections.abc import MutableSequence

    from betty.console import CommandFunction
    from betty.project import Project


@final
@CommandDefinition(
    "about", label=_("Output information about Betty, and optionally your project")
)
class About(Manufacturable, Command):
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
        ui = self._app.ui
        assert isinstance(ui, Console)
        try:
            if project:
                await project.bootstrap()
                await self._about_project(ui, project)
            await self._about_plugins(ui, project)
            await self._about_python_packages(ui)
            await self._about_system(ui)
        finally:
            if project:
                await project.shutdown()

    async def _about_project(self, ui: Console, project: Project) -> None:
        about_project = Table(
            title=ui.localizer.translate._("Your project at {path}").format(
                path=str(project.directory)
            ),
            show_header=False,
        )
        about_project.add_column("", style=self._key_style)
        about_project.add_column("")
        about_project.add_row(
            ui.localizer.translate._("Asset directory"),
            str(project.asset_directory),
        )
        about_project.add_row(
            ui.localizer.translate._("Output directory"),
            str(project.output_directory),
        )
        ui.console.print(about_project, emoji=False, markup=False)

    async def _about_plugins(self, ui: Console, project: Project | None) -> None:
        services = self._app if project is None else project
        about_plugins = Table(title=ui.localizer.translate._("Plugins"))
        about_plugins.add_column(
            ui.localizer.translate._("Type"), style=self._key_style
        )
        about_plugins.add_column(ui.localizer.translate._("ID"))
        about_plugins.add_column(ui.localizer.translate._("Label"))
        for plugin_manager in sorted(
            services.plugins,
            key=lambda plugin_type: plugin_type.type.definition.label.localize(
                ui.localizer
            ),
        ):
            for index, plugin in enumerate(
                sorted([x async for x in plugin_manager], key=lambda plugin: plugin.id)
            ):
                first_column = (
                    plugin_manager.type.definition.label.localize(ui.localizer)
                    if index == 0
                    else ""
                )
                third_column_lines: MutableSequence[str] = []
                if isinstance(plugin, HumanFacingDefinition):
                    third_column_lines.append(plugin.label.localize(ui.localizer))
                about_plugins.add_row(
                    first_column,
                    plugin.id,
                    "\n".join(third_column_lines),
                )
        ui.console.print(about_plugins, emoji=False, markup=False)
        if project is None:
            ui.console.print(
                _(
                    "More plugins may be available when running this command with {argument}."
                )
                .format(argument=Quote("--project"))
                .localize(ui.localizer),
                markup=False,
                style="yellow",
            )

    async def _about_system(self, ui: Console) -> None:
        about_system = Table(
            title=ui.localizer.translate._("System"), show_header=False
        )
        about_system.add_column("", style=self._key_style)
        about_system.add_column("")
        about_system.add_row("Betty", about.version_label)
        about_system.add_row(
            ui.localizer.translate._("Operating system"), platform.platform()
        )
        about_system.add_row("Python", sys.version)
        ui.console.print(about_system, emoji=False, markup=False)

    async def _about_python_packages(self, ui: Console) -> None:
        about_python_packages = Table(title=ui.localizer.translate._("Python packages"))
        about_python_packages.add_column(
            ui.localizer.translate._("Package"), style=self._key_style
        )
        about_python_packages.add_column(ui.localizer.translate._("Version"))
        for x in sorted(
            metadata.distributions(),
            key=lambda x: x.metadata["Name"].lower(),
        ):
            about_python_packages.add_row(x.metadata["Name"], x.version)
        ui.console.print(about_python_packages, emoji=False, markup=False)
