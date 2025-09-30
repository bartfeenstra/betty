from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.assertion import assert_locale_identifier
from betty.console.assertion import assertion_to_argument_type
from betty.console.command import Command, CommandFunction, CommandDefinition
from betty.console.project import add_project_argument
from betty.locale import translation
from betty.locale.localizable import _

if TYPE_CHECKING:
    import argparse

    from betty.app import App
    from betty.project import Project


@final
@CommandDefinition(
    id="new-translation",
    label=_("Create a new translation"),
)
class NewTranslation(AppDependentFactory, Command):
    """
    A command to create a new translation for a project.
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
            "locale",
            type=assertion_to_argument_type(
                assert_locale_identifier(), localizer=localizer
            ),
        )
        return command_function

    async def _command_function(self, project: Project, locale: str) -> None:
        async with project:
            await translation.project.new_project_translation(
                locale, project, user=self._app.user
            )
