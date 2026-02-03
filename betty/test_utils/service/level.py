"""
Test utilities for :py:mod:`betty.service.level`.
"""

from typing import Any, Self

from typing_extensions import override

from betty.service.level import Configurable, ServiceLevel
from betty.test_utils.data import DummyData


class DummyConfigurable(Configurable[DummyData]):
    """
    A dummy :py:class:`betty.service.level.Configurable` implementation.
    """

    def __init__(
        self, *args: Any, configuration: DummyData | None = None, **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.configuration = DummyData() if configuration is None else configuration

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
