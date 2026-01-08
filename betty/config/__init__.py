"""
The Configuration API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, Self

from typing_extensions import TypeVar, override

from betty.data import HasData
from betty.portable import Portable, PortableData

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.data import Sample
    from betty.service.level.factory import ServiceLevelTarget

_PortableDataT = TypeVar("_PortableDataT", bound=PortableData, default=PortableData)


class Configuration(Portable, Generic[_PortableDataT]):
    """
    Any configuration object.
    """

    @override
    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        raise NotImplementedError

    @property
    def validator(self) -> ServiceLevelTarget[None] | None:
        """
        The validator for this configuration, if it can be validated.

        :raises betty.exception.HumanFacingException: Raised if any part of the configuration is invalid.
        """
        return None

    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        """
        Create samples for this configuration.
        """
        return ()


_HasDataT = TypeVar("_HasDataT", bound=HasData | Configuration)


class Configurable(ABC, Generic[_HasDataT]):
    """
    Any configurable object.
    """

    def __init__(self, *args: Any, configuration: _HasDataT, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._configuration = configuration

    @property
    def configuration(self) -> _HasDataT:
        """
        The object's configuration.
        """
        return self._configuration

    @classmethod
    @abstractmethod
    def configuration_cls(cls) -> type[_HasDataT]:
        """
        The object's configuration class.
        """
