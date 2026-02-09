"""
Test utilities for :py:mod:`betty.service.level`.
"""

from typing import Any, Self

from typing_extensions import override

from betty.service.factory import DataManufacturable, Manufacturable
from betty.service.level import ServiceLevel
from betty.test_utils.data import DummyData


class DummyDataManufacturable(DataManufacturable[DummyData], Manufacturable):
    """
    A dummy :py:class:`betty.service.factory.DataManufacturable` implementation.
    """

    def __init__(self, *args: Any, data: DummyData | None = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.data = DummyData() if data is None else data

    @override
    @classmethod
    def new_data_cls(cls) -> type[DummyData]:
        return DummyData

    @override
    @classmethod
    async def new(
        cls, services: ServiceLevel, data: DummyData | None = None, /
    ) -> Self:
        return cls(data=data)
