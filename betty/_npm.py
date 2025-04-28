"""
Provide tools to integrate extensions with `npm <https://www.npmjs.com/>`_.

This module is internal.
"""

from __future__ import annotations

import logging
import sys
from subprocess import CalledProcessError
from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty import subprocess
from betty.error import UserFacingError
from betty.locale.localizable import Localizable, _
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.requirement import Requirement

if TYPE_CHECKING:
    from asyncio import subprocess as aiosubprocess
    from collections.abc import Sequence
    from pathlib import Path

_NPM_SUMMARY_AVAILABLE = _("npm is available")
_NPM_SUMMARY_UNAVAILABLE = _("npm is not available")
_NPM_DETAILS = _(
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


@final
class NpmRequirement(Requirement):
    def __init__(self, met: bool):
        super().__init__()
        self._met = met

    @classmethod
    async def new(cls) -> Self:
        try:
            await npm(["--version"])
        except NpmUnavailable:
            logging.getLogger(__name__).debug(
                _NPM_SUMMARY_UNAVAILABLE.localize(DEFAULT_LOCALIZER)
            )
            logging.getLogger(__name__).debug(_NPM_DETAILS.localize(DEFAULT_LOCALIZER))
            return cls(False)
        except CalledProcessError as error:
            logging.getLogger(__name__).exception(error)
            logging.getLogger(__name__).debug(_NPM_DETAILS.localize(DEFAULT_LOCALIZER))
            return cls(False)
        else:
            return cls(True)

    @override
    def is_met(self) -> bool:
        return self._met

    @override
    def summary(self) -> Localizable:
        if self.is_met():
            return _NPM_SUMMARY_AVAILABLE
        return _NPM_SUMMARY_UNAVAILABLE

    @override
    def details(self) -> Localizable:
        return _NPM_DETAILS
