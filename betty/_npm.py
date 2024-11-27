"""
Provide tools to integrate extensions with `npm <https://www.npmjs.com/>`_.

This module is internal.
"""

from __future__ import annotations

import logging
import sys
from subprocess import CalledProcessError
from typing import Sequence, TYPE_CHECKING

from betty import subprocess
from betty.asyncio import wait_to_thread
from betty.error import UserFacingError
from betty.locale import Str, DEFAULT_LOCALIZER
from betty.requirement import Requirement

if TYPE_CHECKING:
    from pathlib import Path
    from asyncio import subprocess as aiosubprocess

_NPM_SUMMARY_AVAILABLE = Str._("`npm` is available")
_NPM_SUMMARY_UNAVAILABLE = Str._("`npm` is not available")
_NPM_DETAILS = Str._(
    "npm (https://www.npmjs.com/) must be available for features that require Node.js packages to be installed. Ensure that the `npm` executable is available in your `PATH`."
)


class NpmUnavailable(UserFacingError, RuntimeError):
    def __init__(self):
        super().__init__(_NPM_DETAILS)


async def npm(
    arguments: Sequence[str],
    cwd: Path | None = None,
) -> aiosubprocess.Process:
    """
    Run an npm command.
    """
    try:
        return await subprocess.run_process(
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
        self._summary: Str
        self._details = _NPM_DETAILS

    def _check(self) -> None:
        if hasattr(self, "_met"):
            return
        try:
            wait_to_thread(npm(["--version"]))
        except NpmUnavailable:
            self._met = False
            self._summary = _NPM_SUMMARY_UNAVAILABLE
        except CalledProcessError as error:
            logging.getLogger(__name__).exception(error)
            logging.getLogger(__name__).debug(_NPM_DETAILS.localize(DEFAULT_LOCALIZER))
            self._met = False
            self._summary = _NPM_SUMMARY_UNAVAILABLE
        else:
            self._met = True
            self._summary = _NPM_SUMMARY_AVAILABLE
        finally:
            logging.getLogger(__name__).debug(self._summary.localize(DEFAULT_LOCALIZER))

    def is_met(self) -> bool:
        self._check()
        return self._met

    def summary(self) -> Str:
        self._check()
        return self._summary

    def details(self) -> Str:
        return self._details
