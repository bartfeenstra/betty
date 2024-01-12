"""
Provide tools to integrate extensions with `npm <https://www.npmjs.com/>`_.

This extension and module are internal.
"""
from __future__ import annotations

import logging
import sys
from asyncio import subprocess as aiosubprocess
from pathlib import Path
from subprocess import CalledProcessError
from typing import Sequence

from betty.app.extension import Extension
from betty.app.extension.requirement import Requirement, AllRequirements
from betty.asyncio import wait_to_thread
from betty.locale import Str, DEFAULT_LOCALIZER
from betty.subprocess import run_process


async def npm(
    arguments: Sequence[str],
    cwd: Path | None = None,
) -> aiosubprocess.Process:
    """
    Run an npm command.
    """
    return await run_process(
        ['npm', *arguments],
        cwd=cwd,
        # Use a shell on Windows so subprocess can find the executables it needs (see
        # https://bugs.python.org/issue17023).
        shell=sys.platform.startswith('win32'),
    )


class _NpmRequirement(Requirement):
    def __init__(self, met: bool):
        super().__init__()
        self._met = met
        self._summary = self._met_summary() if met else self._unmet_summary()
        self._details = Str._('npm (https://www.npmjs.com/) must be available for features that require Node.js packages to be installed. Ensure that the `npm` executable is available in your `PATH`.')

    @classmethod
    def _met_summary(cls) -> Str:
        return Str._('`npm` is available')

    @classmethod
    def _unmet_summary(cls) -> Str:
        return Str._('`npm` is not available')

    @classmethod
    def check(cls) -> _NpmRequirement:
        try:
            wait_to_thread(npm(['--version']))
            logging.getLogger(__name__).debug(cls._met_summary().localize(DEFAULT_LOCALIZER))
            return cls(True)
        except (CalledProcessError, FileNotFoundError):
            logging.getLogger(__name__).debug(cls._unmet_summary().localize(DEFAULT_LOCALIZER))
            return cls(False)

    def is_met(self) -> bool:
        return self._met

    def summary(self) -> Str:
        return self._summary

    def details(self) -> Str:
        return self._details


class _Npm(Extension):
    _npm_requirement: _NpmRequirement | None = None
    _requirement: Requirement | None = None

    @classmethod
    def _ensure_requirement(cls) -> Requirement:
        if cls._requirement is None:
            cls._requirement = _NpmRequirement.check()
        return cls._requirement

    @classmethod
    def enable_requirement(cls) -> Requirement:
        return AllRequirements(
            cls._ensure_requirement(),
            super().enable_requirement(),
        )
