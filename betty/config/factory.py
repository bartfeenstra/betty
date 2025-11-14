"""
Integrate the configuration and factory APIs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self, TypeVar

from betty.config import Configurable, Configuration

if TYPE_CHECKING:
    from betty.service.level.factory import AnyFactoryTarget

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class ConfigurationDependentSelfFactory(Configurable[_ConfigurationT], ABC):
    """
    Create factories that require configuration.
    """

    @classmethod
    @abstractmethod
    def new_for_configuration(
        cls, configuration: _ConfigurationT
    ) -> AnyFactoryTarget[Self]:
        """
        Create a new factory for the given configuration.
        """
