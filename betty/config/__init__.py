"""
The Configuration API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from betty.mutability import Mutable
from betty.serde.dump import Dumpable
from betty.serde.load import Loadable

if TYPE_CHECKING:
    from betty.service.level.factory import AnyFactoryTarget


class Configuration(Mutable, Loadable, Dumpable):
    """
    Any configuration object.
    """

    @property
    def validator(self) -> AnyFactoryTarget[None] | None:
        """
        The validator for this configuration, if it can be validated.

        :raises betty.exception.HumanFacingException: Raised if any part of the configuration is invalid.
        """
        return None


_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class Configurable(ABC, Generic[_ConfigurationT]):
    """
    Any configurable object.
    """

    def __init__(self, *args: Any, configuration: _ConfigurationT, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._configuration = configuration

    @property
    def configuration(self) -> _ConfigurationT:
        """
        The object's configuration.
        """
        return self._configuration

    @classmethod
    @abstractmethod
    def configuration_cls(cls) -> type[_ConfigurationT]:
        """
        The object's configuration class.
        """
