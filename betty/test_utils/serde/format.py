"""
Test utilities for :py:mod:`betty.serde.format`.
"""

from collections.abc import Sequence

import pytest

from betty.serde.dump import Dump
from betty.serde.format import Format
from betty.test_utils.plugin import PluginTestBase


class FormatTestBase(PluginTestBase[Format]):
    """
    A base class for testing :py:class:`betty.serde.format.Format` implementations.
    """

    def get_format_sut_instances(self) -> Sequence[Format]:
        """
        Produce instances of the plugin under test.
        """
        raise NotImplementedError

    def test_extensions(self) -> None:
        """
        Tests :py:meth:`betty.serde.format.Format.extensions` implementations.
        """
        extensions = self.get_sut_class().extensions()
        assert extensions
        for extension in extensions:
            assert len(extension) > 2
            assert extension.startswith(".")

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
    def test_dump_and_load(self, dump: Dump) -> None:
        """
        Tests :py:meth:`betty.serde.format.Format.load` and :py:meth:`betty.serde.format.Format.dump` implementations.
        """
        for sut in self.get_format_sut_instances():
            assert sut.load(sut.dump(dump)) == dump

    def test_load(self) -> None:
        """
        Satisfy :py:class:`betty.tests.coverage.test_coverage.TestCoverage`.
        """
