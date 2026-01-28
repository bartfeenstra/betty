"""
Test utilities for :py:mod:`betty.config`.
"""

from typing_extensions import override

from betty.config import Configurable
from betty.test_utils.data import DummyData


class DummyConfigurable(Configurable[DummyData]):
    """
    A dummy :py:class:`betty.config.Configurable` implementation.
    """

    @override
    @classmethod
    def configuration_cls(cls) -> type[DummyData]:
        return DummyData
