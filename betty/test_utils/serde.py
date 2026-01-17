"""
Test utilities for :py:mod:`betty.serde`.
"""

import pytest

from betty.portable import PortableData
from betty.serde import Serializer
from betty.test_utils.plugin import PluginTestBase
from betty.test_utils.plugin.human_facing import HumanFacingPluginDefinitionTestBase


class SerializerDefinitionTestBase(HumanFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.serde.SerializerDefinition` subclasses.
    """


class SerializerTestBase(PluginTestBase[Serializer]):
    """
    A base class for testing :py:class:`betty.serde.Serializer` implementations.
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
    def test_dump_and_load(self, portable: PortableData, sut: Serializer) -> None:
        """
        Tests :py:meth:`betty.serde.Serializer.load` and :py:meth:`betty.serde.Serializer.dump` implementations.
        """
        assert sut.load(sut.dump(portable)) == portable

    def test_load(self) -> None:
        """
        Satisfy ``TestCoverage``.
        """
