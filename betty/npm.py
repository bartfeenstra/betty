"""
Provide tools to integrate extensions with `npm <https://www.npmjs.com/>`_.

This module is internal.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, final

from betty import subprocess
from betty.locale.localizable.gettext import _
from betty.requirement import UnmetRequirement

if TYPE_CHECKING:
    from asyncio import subprocess as aiosubprocess
    from collections.abc import Sequence
    from pathlib import Path

    from betty.user import User


@final
class NpmUnavailable(UnmetRequirement, RuntimeError):
    """
    An error raised when npm is unavailable.
    """

    def __init__(self):
        super().__init__(
            _(
                "npm (https://www.npmjs.com/) must be available for features that require Node.js packages to be installed. Ensure that the `npm` executable is available in your `PATH`."
            )
        )


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
