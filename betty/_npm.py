"""
Provide tools to integrate extensions with `npm <https://www.npmjs.com/>`_.

This module is internal.
"""

from __future__ import annotations

import logging
import sys
from typing import Sequence, TYPE_CHECKING

from betty.error import UserFacingError
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.locale.localizable import _, Localizable
from betty.requirement import Requirement
from betty.subprocess import run_process

if TYPE_CHECKING:
    from pathlib import Path
    from asyncio import subprocess as aiosubprocess


_NPM_UNAVAILABLE_MESSAGE = _(
    "npm (https://www.npmjs.com/) must be available for features that require Node.js packages to be installed. Ensure that the `npm` executable is available in your `PATH`."
)


class NpmUnavailable(UserFacingError, RuntimeError):
    def __init__(self):
        super().__init__(_NPM_UNAVAILABLE_MESSAGE)


async def npm(
    arguments: Sequence[str],
    cwd: Path | None = None,
) -> aiosubprocess.Process:
    """
    Run an npm command.
    """
    try:
        return await run_process(
            ["npm", *arguments],
            cwd=cwd,
            # Use a shell on Windows so subprocess can find the executables it needs (see
            # https://bugs.python.org/issue17023).
            shell=sys.platform.startswith("win32"),
        )
    except FileNotFoundError:
        raise NpmUnavailable() from None


class NpmRequirement(Requirement):
    def __init__(self):
        super().__init__()
        self._met: bool
        self._summary: Localizable
        self._details = _NPM_UNAVAILABLE_MESSAGE

    async def _check(self) -> None:
        if hasattr(self, "_met"):
            return
        try:
            await npm(["--version"])
        except NpmUnavailable:
            self._met = False
            self._summary = _("`npm` is not available")
        else:
            self._met = True
            self._summary = _("`npm` is available")
        finally:
            logging.getLogger(__name__).debug(self._summary.localize(DEFAULT_LOCALIZER))

    async def is_met(self) -> bool:
        await self._check()
        return self._met

    async def summary(self) -> Localizable:
        await self._check()
        return self._summary

    async def details(self) -> Localizable:
        return self._details
