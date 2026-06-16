"""
Test utilities for :py:mod:`betty.machine_name`.
"""

from collections.abc import Sequence
from typing import Final

VALID_MACHINE_NAMES: Final[Sequence[str]] = (
    "a",
    "-a",
    "a-",
    "-a-",
    "a-b",
    "-a-b",
    "a-b-",
    "-a-b-",
    "a-b-c",
    "abc1234567890",
    # A UUID4.
    "9e3b550e-4263-4c49-a288-d6c6b585722a",
    # Name is exactly 250 characters.
    "machinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachi",
)
INVALID_MACHINE_NAMES: Final[Sequence[str]] = (
    # Consecutive dashes.
    "--a",
    "a--",
    "--a--",
    "a--b",
    "--a-b",
    "-a-b--",
    # Underscores.
    "package_machine",
    "package_module_machine",
    # An empty name.
    "",
    # Name exceeds 250 characters.
    "machinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachinemachin",
)
