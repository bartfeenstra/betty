"""
JSON schemas for the privacy API.
"""

from __future__ import annotations

from typing import final

from betty.classtools import Singleton
from betty.json.schema import Boolean


@final
class PrivacySchema(Singleton, Boolean):
    """
    A JSON Schema for privacy.
    """

    def __init__(self):
        super().__init__(
            def_name="privacy",
            title="Privacy",
            description="Whether this entity is private (true), or public (false).",
        )
