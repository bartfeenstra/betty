"""
Test utilities for :py:mod:`betty.content_provider`.
"""

from __future__ import annotations

from betty.content_provider import ContentProvider
from betty.test_utils.plugin import PluginTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase


class ContentProviderDefinitionTestBase(HumanFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.content_provider.ContentProviderDefinition` implementations.
    """


class ContentProviderTestBase(PluginTestBase[ContentProvider]):
    """
    A base class for testing :py:class:`betty.content_provider.ContentProvider` implementations.
    """
