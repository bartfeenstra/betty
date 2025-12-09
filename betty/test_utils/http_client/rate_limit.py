"""
Test utilities for :py:mod:`betty.http_client.rate_limit`.
"""

from betty.http_client.rate_limit import RateLimit
from betty.test_utils.plugin import PluginTestBase
from betty.test_utils.plugin.ordered import OrderedPluginDefinitionTestBase


class RateLimitDefinitionTestBase(OrderedPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.http_client.rate_limit.RateLimitDefinition` subclasses.
    """


class RateLimitTestBase(PluginTestBase[RateLimit]):
    """
    A base class for testing :py:class:`betty.http_client.rate_limit.RateLimit` implementations.
    """
