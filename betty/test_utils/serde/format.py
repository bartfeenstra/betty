"""
Test utilities for :py:mod:`betty.serde.format`.
"""

import pytest

from betty.serde.dump import Dump
from betty.serde.format import Format
from betty.test_utils.plugin.classed import ClassedPluginDefinitionTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase


class FormatPluginTestBase(
    HumanFacingPluginDefinitionTestBase, ClassedPluginDefinitionTestBase
):
    """
    A base class for testing :py:class:`betty.serde.format.FormatPlugin` subclasses.
    """


class FormatTestBase:
    """
    A base class for testing :py:class:`betty.serde.format.Format` implementations.
    """

    @pytest.fixture
    def sut(self) -> Format:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

    @pytest.mark.parametrize(
        "dump",
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
    def test_dump_and_load(self, dump: Dump, sut: Format) -> None:
        """
        Tests :py:meth:`betty.serde.format.Format.load` and :py:meth:`betty.serde.format.Format.dump` implementations.
        """
        assert sut.load(sut.dump(dump)) == dump

    def test_load(self) -> None:
        """
        Satisfy :py:class:`betty.tests.coverage.test_coverage.TestCoverage`.
        """
