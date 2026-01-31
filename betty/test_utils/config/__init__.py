"""
Test utilities for :py:mod:`betty.config`.
"""

from typing import Any, Self

from typing_extensions import override

from betty.config import Configurable
from betty.service.level import ServiceLevel
from betty.test_utils.data import DummyData


class DummyConfigurable(Configurable[DummyData]):
    """
    A dummy :py:class:`betty.config.Configurable` implementation.
    """

    def __init__(self, *args: Any, configuration: DummyData | None, **kwargs: Any):
        super().__init__(
            *args,
            configuration=DummyData() if configuration is None else configuration,
            **kwargs,
        )

    @override
    @classmethod
    def configuration_cls(cls) -> type[DummyData]:
        return DummyData

    @override
    @classmethod
    async def new_for_configuration(
        cls, *, services: ServiceLevel, configuration: DummyData | None = None
    ) -> Self:
        return cls(configuration=configuration)
