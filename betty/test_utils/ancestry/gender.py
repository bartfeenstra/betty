"""
Test utilities for :py:mod:`betty.ancestry.gender`.
"""

from __future__ import annotations

from betty.ancestry.gender import Gender
from betty.test_utils.plugin import DummyPluginBase, PluginTestBase


class GenderTestBase(PluginTestBase[Gender]):
    """
    A base class for testing :py:class:`betty.ancestry.gender.Gender` implementations.
    """


class DummyGender(DummyPluginBase, Gender):
    """
    A dummy gender implementation.
    """
