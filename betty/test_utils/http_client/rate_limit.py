"""
Test utilities for :py:mod:`betty.http_client.rate_limit`.
"""

from betty.test_utils.plugin.ordered import OrderedPluginDefinitionTestBase


class RateLimitDefinitionTestBase(OrderedPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.http_client.rate_limit.RateLimitDefinition` subclasses.
    """
