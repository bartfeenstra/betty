from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

from typing_extensions import override
from textual.widgets import RichLog
from betty.app.factory import AppDependentFactory
from betty.console.command import Command, CommandFunction
from betty.desktop import BettyApp
from betty.desktop.user import DesktopUser
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    import argparse

    from betty.app import App


@final
class Desktop(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to launch the Betty desktop application.
    """

    _plugin_id = "desktop"
    _plugin_label = _("Launch the desktop applications")

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
        log = RichLog()
        await self._app.set_user(DesktopUser(log))
        app = BettyApp(self._app)
        await app.run_async()
