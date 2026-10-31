from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager
from typing import TYPE_CHECKING, Self, final, override

from betty.app import App
from betty.console import Command, CommandExit, CommandExitCode
from betty.factory import Manufacturable
from betty.requirements._dev import require_dev
from betty.sys import ExitCode

if TYPE_CHECKING:
    from collections.abc import Generator


class DevCommand(Manufacturable, Command):
    @final
    def __init__(self, app: App, /):
        self._app = app

    @override
    @App.require
    @require_dev
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls(app)

    @contextmanager
    def _exit(
        self, code: CommandExitCode, *exceptions: type[Exception]
    ) -> Generator[None]:
        try:
            yield
        except exceptions as exception:
            raise CommandExit(code) from exception

    def _error_unexpected_recoverable(
        self, *exceptions: type[Exception]
    ) -> AbstractContextManager[None]:
        return self._exit(ExitCode.ERROR_UNEXPECTED_RECOVERABLE, *exceptions)
