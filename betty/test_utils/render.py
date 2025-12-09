"""
Test utilities for :py:mod:`betty.render`.
"""

from __future__ import annotations

from betty.render import Renderer
from betty.test_utils.plugin import PluginDefinitionTestBase, PluginTestBase


class RendererDefinitionTestBase(PluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.render.RendererDefinition` implementations.
    """


class RendererTestBase(PluginTestBase[Renderer]):
    """
    A base class for testing :py:class:`betty.render.Renderer` implementations.
    """
