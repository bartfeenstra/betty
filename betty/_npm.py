"""
Provide tools to integrate extensions with `npm <https://www.npmjs.com/>`_.

This module is internal.
"""

from __future__ import annotations

import sys
from subprocess import CalledProcessError
from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty import subprocess
from betty.exception import HumanFacingException
from betty.locale.localizable import Localizable, _
from betty.requirement import Requirement

if TYPE_CHECKING:
    from asyncio import subprocess as aiosubprocess
    from collections.abc import Sequence
    from pathlib import Path

    from betty.user import User

_NPM_SUMMARY_AVAILABLE = _("npm is available")
_NPM_SUMMARY_UNAVAILABLE = _("npm is not available")
_NPM_DETAILS = _(
    "npm (https://www.npmjs.com/) must be available for features that require Node.js packages to be installed. Ensure that the `npm` executable is available in your `PATH`."
)


class NpmUnavailable(HumanFacingException, RuntimeError):
    def __init__(self):
        super().__init__(_NPM_DETAILS)


async def npm(
    arguments: Sequence[str], cwd: Path | None = None, *, user: User
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
            user=user,
        )
    except FileNotFoundError:
        raise NpmUnavailable() from None


@final
class NpmRequirement(Requirement):
    def __init__(self, met: bool):
        super().__init__()
        self._met = met

    @classmethod
    async def new(cls, *, user: User) -> Self:
        try:
            await npm(["--version"], user=user)
        except NpmUnavailable:
            await user.message_debug(_NPM_SUMMARY_UNAVAILABLE)
            await user.message_debug(_NPM_DETAILS)
            return cls(False)
        except CalledProcessError:
            await user.message_exception()
            await user.message_debug(_NPM_DETAILS)
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
