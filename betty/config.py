"""
The Configuration API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    ParamSpec,
    Self,
)

from typing_extensions import TypeVar

from betty.data import Data
from betty.portable import PortableData

if TYPE_CHECKING:
    from betty.service.level import ServiceLevel

_PortableDataT = TypeVar("_PortableDataT", bound=PortableData, default=PortableData)


_T = TypeVar("_T")
_P = ParamSpec("_P")
_DataT = TypeVar("_DataT", bound=Data, default=Data)


class HasConfiguration(ABC, Generic[_DataT]):
    """
    An object with configuration.
    """

    def __init__(self, *args: Any, configuration: _DataT, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._configuration = configuration

    @property
    def configuration(self) -> _DataT:
        """
        The object's configuration.
        """
        return self._configuration

    @classmethod
    @abstractmethod
    def configuration_cls(cls) -> type[_DataT]:
        """
        The object's configuration class.
        """


class Configurable(HasConfiguration[_DataT]):
    """
    Any configurable object.
    """

    @classmethod
    @abstractmethod
    async def new_for_configuration(
        cls, *, services: ServiceLevel, configuration: _DataT
    ) -> Self:
        """
        Create a new instance using the given service level and configuration.
        """
