"""
Test utilities for :py:mod:`betty.serde`.
"""

import pytest

from betty.portable import PortableData
from betty.serde import Format
from betty.test_utils.plugin import PluginTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase


class FormatDefinitionTestBase(HumanFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.serde.FormatDefinition` subclasses.
    """


class FormatTestBase(PluginTestBase[Format]):
    """
    A base class for testing :py:class:`betty.serde.Format` implementations.
    """

    @pytest.mark.parametrize(
        "portable",
        [
            True,
            False,
            None,
            "abc",
            123,
            {},
            {"key": "value"},
            [],
            ["value"],
        ],
    )
    def test_dump_and_load(self, portable: PortableData, sut: Format) -> None:
        """
        Tests :py:meth:`betty.serde.Format.load` and :py:meth:`betty.serde.Format.dump` implementations.
        """
        assert sut.load(sut.dump(portable)) == portable

    def test_load(self) -> None:
        """
        Satisfy :py:class:`betty.tests.coverage.test_coverage.TestCoverage`.
        """
