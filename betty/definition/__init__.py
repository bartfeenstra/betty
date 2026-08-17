"""
Tools to create definition classes.
"""

from __future__ import annotations

from typing import Never

from betty.capability import HasCapabilities, Stage


class Definition[StageT: Stage = Never](HasCapabilities[StageT]):
    """
    A definition.
    """
