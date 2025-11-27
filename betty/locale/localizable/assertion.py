"""
Provide localizable assertions.
"""

from __future__ import annotations

from betty.assertion import AssertionChain
from betty.locale.localizable.config import load_localizable

assert_load_localizable = AssertionChain(load_localizable)
"""
Load a localizable from configuration.
"""
