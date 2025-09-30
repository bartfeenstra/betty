from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.assertion import (
    assert_or,
    assert_none,
    assert_directory_path,
)
from betty.console.assertion import assertion_to_argument_type
from betty.console.command import Command, CommandFunction, CommandDefinition
from betty.console.project import add_project_argument
from betty.locale import translation
from betty.locale.localizable import _

if TYPE_CHECKING:
    import argparse
    from pathlib import Path

    from betty.app import App
    from betty.project import Project


@final
@CommandDefinition(
    id="update-translations",
    label=_("Update all existing translations"),
)
class UpdateTranslations(AppDependentFactory, Command):
    """
    A command to update all of a project's translations.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        localizer = await self._app.localizer
        command_function = await add_project_argument(
            parser, self._command_function, self._app
        )
        parser.add_argument(
            "--source",
            type=assertion_to_argument_type(
                assert_or(assert_none(), assert_directory_path()), localizer=localizer
            ),
        )
        parser.add_argument(
            "--exclude",
            action="append",
            type=assertion_to_argument_type(
                assert_directory_path(), localizer=localizer
            ),
        )
        return command_function

    async def _command_function(
        self, project: Project, source: Path | None, exclude: tuple[Path] | None
    ) -> None:
        async with project:
            await translation.project.update_project_translations(
                project.configuration.project_directory_path,
                source,
                None if exclude is None else set(exclude),
            )
