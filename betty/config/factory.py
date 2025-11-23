"""
Integrate the configuration and factory APIs.
"""

from abc import abstractmethod
from typing import Generic, Self, TypeVar

from betty.config import Configuration
from betty.requirement import HasRequirement
from betty.service.level import AnyFactoryTarget

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class ConfigurationDependentFactory(Generic[_ConfigurationT], HasRequirement):
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
