from __future__ import annotations  # noqa: D100

from pathlib import Path
from typing import TYPE_CHECKING, Self, final, override

from aiofiles.os import makedirs
from aiofiles.tempfile import TemporaryDirectory

from betty import dirs
from betty.about import IS_DEVELOPMENT
from betty.app import App
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.demo.generate import generate_with_cleanup
from betty.demo.project import create_project
from betty.job import Context
from betty.requirement import UnmetRequirement
from betty.service.factory import Manufacturable

if TYPE_CHECKING:
    import argparse
    from collections.abc import Iterable

    from yappi import YFuncStats

    from betty.plugin.discovery import ResolvableDiscovery
    from betty.service.level import ServiceLevel
    from betty.user import User


async def _target(user: User) -> None:
    async with (
        App.new_isolated() as app,
        TemporaryDirectory() as project_directory_path_str,
    ):
        project = await create_project(app, Path(project_directory_path_str))
        async with project, user.message_progress("Generating site...") as progress:
            await generate_with_cleanup(project, context=Context(progress=progress))


def _print(stats: YFuncStats, sort_column: str, sort_direction: str) -> None:
    stats.sort(sort_column, sort_direction)
    stats.print_all(
        columns={
            0: ("tsub", 10),
            1: ("ttot", 10),
            2: ("tavg", 10),
            3: ("ncall", 10),
            4: ("name", 99),
        }
    )


@final
@CommandDefinition(
    "dev-profile-demo", label="Profile the generation of the demonstration site"
)
class DevProfileDemo(Manufacturable, Command):
    """
    .. plugin:: command:dev-profile-demo.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        parser.set_defaults(
            clock_type="CPU",
            force=False,
            sort_column="tsub",
            sort_direction="asc",
        )
        clock_type_group = parser.add_mutually_exclusive_group()
        clock_type_group.add_argument(
            "--cpu",
            dest="clock_type",
            action="store_const",
            const="CPU",
            help="Use the cpu clock",
        )
        clock_type_group.add_argument(
            "--wall",
            dest="clock_type",
            action="store_const",
            const="WALL",
            help="Use the wall clock",
        )
        sort_column_group = parser.add_mutually_exclusive_group()
        sort_column_group.add_argument(
            "--tsub",
            dest="sort_column",
            action="store_const",
            const="tsub",
            help="Sort on the `tsub` column",
        )
        sort_column_group.add_argument(
            "--ttot",
            dest="sort_column",
            action="store_const",
            const="ttot",
            help="Sort on the `ttot` column",
        )
        sort_column_group.add_argument(
            "--tavg",
            dest="sort_column",
            action="store_const",
            const="tavg",
            help="Sort on the `tavg` column",
        )
        sort_column_group.add_argument(
            "--ncall",
            dest="sort_column",
            action="store_const",
            const="ncall",
            help="Sort on the `ncall` column",
        )
        sort_column_group.add_argument(
            "--name",
            dest="sort_column",
            action="store_const",
            const="name",
            help="Sort on the `name` column",
        )
        sort_direction_group = parser.add_mutually_exclusive_group()
        sort_direction_group.add_argument(
            "--asc",
            dest="sort_direction",
            action="store_const",
            const="asc",
            help="Sort results in ascending order",
        )
        sort_direction_group.add_argument(
            "--desc",
            dest="sort_direction",
            action="store_const",
            const="desc",
            help="Sort results in descending order",
        )
        parser.add_argument(
            "--force",
            dest="force",
            action="store_true",
            help="Ignore the cache and create new profiling stats",
            default=False,
        )
        return self._command_function

    async def _command_function(
        self, *, clock_type: str, force: bool, sort_column: str, sort_direction: str
    ) -> None:
        import yappi

        stats_file_path = (
            dirs.DEV_OUTPUT_DIRECTORY_PATH / f"{self.plugin().id}-{clock_type}.ystats"
        )
        if not force and stats_file_path.exists():
            stats = yappi.get_func_stats()
            stats.add([stats_file_path])
            _print(stats, sort_column, sort_direction)
            await self._app.user.message_information(
                f"Showing existing stats from {stats_file_path}"
            )
        else:
            await makedirs(stats_file_path.parent, exist_ok=True)
            yappi.set_clock_type(clock_type)  # Use set_clock_type("wall") for wall time
            yappi.start()
            await _target(self._app.user)
            yappi.stop()
            stats = yappi.get_func_stats()
            stats.save(stats_file_path)
            _print(stats, sort_column, sort_direction)
            await self._app.user.message_information(
                f"Showing newly generated stats from {stats_file_path}"
            )


def _discover(_: ServiceLevel) -> Iterable[ResolvableDiscovery[CommandDefinition]]:
    if not IS_DEVELOPMENT:
        raise UnmetRequirement("This is only available when developing Betty")
    yield DevProfileDemo
