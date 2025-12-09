"""
Provide tools to integrate extensions with `npm <https://www.npmjs.com/>`_.

This module is internal.
"""

from __future__ import annotations

import sys
from subprocess import CalledProcessError
from typing import TYPE_CHECKING

from betty import subprocess
from betty.exception import HumanFacingException
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Paragraph
from betty.requirement import Requirement, StaticRequirement

if TYPE_CHECKING:
    from asyncio import subprocess as aiosubprocess
    from collections.abc import Sequence
    from pathlib import Path

    from betty.user import User

_NPM_REQUIREMENT_SUMMARY = _("npm is not available")
_NPM_REQUIREMENT_DETAILS = _(
    "npm (https://www.npmjs.com/) must be available for features that require Node.js packages to be installed. Ensure that the `npm` executable is available in your `PATH`."
)


class NpmUnavailable(HumanFacingException, RuntimeError):
    def __init__(self):
        super().__init__(_NPM_REQUIREMENT_DETAILS)


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


async def is_available(*, user: User) -> bool:
    try:
        await npm(["--version"], user=user)
        return True
    except NpmUnavailable:
        pass
    except CalledProcessError:
        await user.message_exception()
    await user.message_debug(
        Paragraph(_NPM_REQUIREMENT_SUMMARY, _NPM_REQUIREMENT_DETAILS)
    )
    return False


async def new_npm_requirement(*, user: User) -> Requirement | None:
    if await is_available(user=user):
        return None
    return StaticRequirement(_NPM_REQUIREMENT_SUMMARY, _NPM_REQUIREMENT_DETAILS)
