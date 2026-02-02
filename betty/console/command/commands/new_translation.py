from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.argparse import assertion_to_argument_type
from betty.assertion import assert_locale
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.console.project import add_project_argument
from betty.locale.localizable.gettext import _
from betty.locale.translation import project as translation_project
from betty.service.level import Manufacturable
from betty.service.requirement.app import require_app

if TYPE_CHECKING:
    import argparse

    from babel import Locale

    from betty.app import App
    from betty.project import Project


@final
@CommandDefinition("new-translation", label=_("Create a new translation"))
class NewTranslation(Manufacturable, Command):
    """
    .. plugin:: command:new-translation.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    @require_app
    async def new_for_services(cls, *, app: App) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        localizer = await self._app.localizer
        command_function = await add_project_argument(
            parser, self._command_function, self._app
        )
        parser.add_argument(
            "locale",
            type=assertion_to_argument_type(assert_locale(), localizer=localizer),
        )
        return command_function

    async def _command_function(self, project: Project, locale: Locale) -> None:
        async with project:
            await translation_project.new_project_translation(
                locale, project, user=self._app.user
            )
