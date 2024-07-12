"""
Integrate the Locale API with Babel.
"""

from __future__ import annotations

from asyncio import to_thread
from contextlib import redirect_stderr
from io import StringIO

from babel.messages.frontend import CommandLineInterface


def _run_babel(*args: str) -> None:
    with redirect_stderr(StringIO()):
        CommandLineInterface().run(list(args))


async def run_babel(*args: str) -> None:
    """
    Run a Babel Command Line Interface (CLI) command.
    """
    await to_thread(_run_babel, *args)
