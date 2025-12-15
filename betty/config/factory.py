"""
Integrate the configuration and factory APIs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self, TypeVar

from betty.config import Configurable, Configuration
from betty.exception import HumanFacingException
from betty.factory import FactoryError
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.typing import Void

if TYPE_CHECKING:
    from betty.serde.dump import Dump
    from betty.service.level.factory import AnyFactoryTarget

_T = TypeVar("_T")
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


class _HumanFacingFactoryError(FactoryError, HumanFacingException):
    pass


def new_target(
    target: ConfigurationDependentSelfFactory[Configuration] | AnyFactoryTarget[_T],
    configuration: Configuration | Dump | Void = Void(),  # noqa B008
    /,
) -> AnyFactoryTarget[_T]:
    """
    Create a new instance of a potentially configurable target.

    :raises FactoryError: raised when ``target`` could not be called.
    """
    if not isinstance(configuration, Void):
        if not isinstance(target, type) or not issubclass(target, Configurable):
            raise _HumanFacingFactoryError(
                _(
                    '"{target}" is not configurable, but configuration was given.'
                ).format(target=fully_qualified_name(target))
            )
        if not issubclass(target, ConfigurationDependentSelfFactory):
            raise FactoryError(
                f"Cannot instantiate {fully_qualified_name(target)} with configuration because it does not subclass {fully_qualified_name(ConfigurationDependentSelfFactory)}."
            )
        if isinstance(configuration, Configuration):
            if not isinstance(configuration, target.configuration_cls()):
                raise FactoryError(
                    f"{fully_qualified_name(target)} required {fully_qualified_name(target.configuration_cls())}, but {fully_qualified_name(type(configuration))} was given."
                )
        else:
            configuration = target.configuration_cls().load(configuration)
        return target.new_for_configuration(configuration)  # type: ignore[return-value]
    return target  # type: ignore[return-value]
