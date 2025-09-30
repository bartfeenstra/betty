from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.console.command import Command, CommandFunction, CommandDefinition
from betty.locale.localizable import _
from betty.project import new

if TYPE_CHECKING:
    import argparse

    from betty.app import App


@final
@CommandDefinition(
    id="new",
    label=_("Create a new project"),
)
class New(AppDependentFactory, Command):
    """
    A command to create a new project.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        return self._command_function

    async def _command_function(self) -> None:
        await new.new(self._app)
