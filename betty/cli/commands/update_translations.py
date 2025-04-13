from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

import asyncclick as click
from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.assertion import (
    assert_or,
    assert_none,
    assert_directory_path,
    assert_sequence,
)
from betty.cli.commands import command, Command, parameter_callback, project_option
from betty.locale import translation
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    from pathlib import Path

    from betty.app import App
    from betty.project import Project


@final
class UpdateTranslations(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to update all of a project's translations.
    """

    _plugin_id = "update-translations"
    _plugin_label = _("Update all existing translations")

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @override
    async def click_command(self) -> click.Command:
        localizer = await self._app.localizer
        description = self.plugin_description()

        @command(
            self.plugin_id(),
            short_help=self.plugin_label().localize(localizer),
            help=description.localize(localizer)
            if description
            else self.plugin_label().localize(localizer),
        )
        @click.option(
            "--source",
            callback=parameter_callback(
                assert_or(assert_none(), assert_directory_path())
            ),
        )
        @click.option(
            "--exclude",
            multiple=True,
            callback=parameter_callback(assert_sequence(assert_directory_path())),
        )
        @project_option
        async def update_translations(
            project: Project, source: Path | None, exclude: tuple[Path]
        ) -> None:
            await translation.update_project_translations(
                project.configuration.project_directory_path, source, set(exclude)
            )

        return update_translations
