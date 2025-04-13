from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

import asyncclick as click
from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.assertion import assert_locale_identifier
from betty.cli.commands import command, Command, parameter_callback, project_option
from betty.locale import translation
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    from betty.app import App
    from betty.project import Project


@final
class NewTranslation(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to create a new translation for a project.
    """

    _plugin_id = "new-translation"
    _plugin_label = _("Create a new translation")

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
        @click.argument(
            "locale",
            required=True,
            callback=parameter_callback(assert_locale_identifier()),
        )
        @project_option
        async def new_translation(project: Project, locale: str) -> None:
            await translation.new_project_translation(locale, project)

        return new_translation
