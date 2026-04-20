"""
Test utilities for :py:mod:`betty.extension`.
"""

from typing import final

from betty.extension import Extension, ExtensionDefinition


class _DummyExtension(Extension):
    pass


@final
@ExtensionDefinition("dummy-one", label="Dummy One")
class DummyExtensionOne(_DummyExtension):
    """
    A dummy :py:class:`betty.extension.Extension` implementation.
    """


@final
@ExtensionDefinition("dummy-two", label="Dummy Two")
class DummyExtensionTwo(_DummyExtension):
    """
    A dummy :py:class:`betty.extension.Extension` implementation.
    """
