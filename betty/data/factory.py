"""
Data-based object factories.
"""

from __future__ import annotations

from abc import abstractmethod

from betty.data import Data
from betty.factory import Arg2Manufacturable
from betty.service_level import ServiceLevel


class DataManufacturable[ServiceLevelT: ServiceLevel, DataT: Data](
    Arg2Manufacturable[ServiceLevelT, DataT]
):
    """
    A class that can be initialized using defined data.
    """

    @classmethod
    @abstractmethod
    def new_data_cls(cls) -> type[DataT]:
        """
        The object's defined data class.
        """
