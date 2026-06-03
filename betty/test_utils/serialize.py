"""
Test utilities for :py:mod:`betty.serialize`.
"""

import pytest

from betty.portable import PortableData
from betty.serialize import Serializer


class SerializerTestBase[SerializerT: Serializer]:
    """
    A base class for testing :py:class:`betty.serialize.Serializer` implementations.
    """

    @pytest.fixture
    def sut(self) -> type[SerializerT]:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

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
    def test_dump_and_load(self, portable: PortableData, sut: SerializerT) -> None:
        """
        Tests :py:meth:`betty.serialize.Serializer.load` and :py:meth:`betty.serialize.Serializer.dump` implementations.
        """
        assert sut.load(sut.dump(portable)) == portable

    def test_load(self) -> None:
        """
        Satisfy :py:class:`betty.tests.coverage.test_coverage.TestCoverage`.
        """
