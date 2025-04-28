"""
Test utilities for :py:mod:`betty.ancestry.gender`.
"""

from __future__ import annotations

from betty.ancestry.gender import Gender
from betty.test_utils.plugin import (
    DummyPlugin,
    PluginTestBase,
)


class GenderTestBase(PluginTestBase[Gender]):
    """
    A base class for testing :py:class:`betty.ancestry.gender.Gender` implementations.
    """


class DummyGender(DummyPlugin, Gender):
    """
    A dummy gender implementation.
    """
