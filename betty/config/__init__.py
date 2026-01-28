"""
The Configuration API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic

from typing_extensions import TypeVar

from betty.data import Data
from betty.portable import PortableData

_PortableDataT = TypeVar("_PortableDataT", bound=PortableData, default=PortableData)


_DataClsT = TypeVar("_DataClsT", bound=Data)


class Configurable(ABC, Generic[_DataClsT]):
    """
    Any configurable object.
    """

    def __init__(self, *args: Any, configuration: _DataClsT, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._configuration = configuration

    @property
    def configuration(self) -> _DataClsT:
        """
        The object's configuration.
        """
        return self._configuration

    @classmethod
    @abstractmethod
    def configuration_cls(cls) -> type[_DataClsT]:
        """
        The object's configuration class.
        """
