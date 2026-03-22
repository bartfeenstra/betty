from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Self, final, override

from betty.app import App
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.locale.localizable.gettext import _
from betty.project import new
from betty.requirement import require
from betty.service.factory import Manufacturable

if TYPE_CHECKING:
    import argparse


@final
@CommandDefinition("new", label=_("Create a new project"))
class New(Manufacturable, Command):
    """
    .. plugin:: command:new.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    @require(App)
    async def new(cls, app: App, /) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        return self._command_function

    async def _command_function(self) -> None:
        await new.new(self._app)
