"""
Data-based object factories.
"""

from __future__ import annotations

from abc import abstractmethod

from betty.data import Data
from betty.factory import Manufacturable
from betty.service_level import ServiceLevel


# @todo Radical thought:
# @todo - What if we take manufacturing out of this, and this just becomes a class to expose a data/configuration class.
# @todo -
# @todo
# @todo
# @todo Keep in mind:
# @todo - Some plugins need nothing (__init__())
# @todo - Some plugins need something from the environment, but async ((new())
# @todo - Some need just their data, and no integration (__init__(data)) or new(data))
# @todo - Some need just their data as well as integration (__init__(services, data)) or new(services, data))
# @todo
# @todo HOWEVER: this is really an integration API anyway, and we want to discourage developers from injecting
# @todo service levels or data into their __init__() (because coupling), so maybe we should indeed NEVER EVER
# @todo call __init__() with arguments anyway?
# @todo
# @todo
# @todo
# @todo
class DataManufacturable[ServiceLevelT: ServiceLevel, DataT: Data](
    Manufacturable[ServiceLevelT, DataT]
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
