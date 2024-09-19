"""
Test utilities for :py:mod:`betty.copyright`.
"""

from __future__ import annotations

from typing_extensions import override

from betty.copyright import Copyright
from betty.locale.localizable import Localizable, plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.test_utils.plugin import (
    DummyPlugin,
    PluginInstanceTestBase,
)


class CopyrightTestBase(PluginInstanceTestBase[Copyright]):
    """
    A base class for testing :py:class:`betty.copyright.Copyright` implementations.
    """

    def test_summary(self) -> None:
        """
        Tests :py:meth:`betty.copyright.Copyright.summary` implementations.
        """
        for sut in self.get_sut_instances():
            assert sut.summary.localize(DEFAULT_LOCALIZER)

    def test_text(self) -> None:
        """
        Tests :py:meth:`betty.copyright.Copyright.text` implementations.
        """
        for sut in self.get_sut_instances():
            assert sut.summary.localize(DEFAULT_LOCALIZER)


class DummyCopyright(DummyPlugin, Copyright):
    """
    A dummy copyright implementation.
    """

    @override
    @property
    def summary(self) -> Localizable:
        return plain("")

    @override
    @property
    def text(self) -> Localizable:
        return plain("")
