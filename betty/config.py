"""
The Configuration API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, Self, cast

from typing_extensions import TypeVar

from betty.data import Data
from betty.exception import HumanFacingException
from betty.factory import FactoryError
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.portable import PortableData
from betty.typing import Void

if TYPE_CHECKING:
    from betty.service.level.factory import ServiceLevelTarget

_PortableDataT = TypeVar("_PortableDataT", bound=PortableData, default=PortableData)


_T = TypeVar("_T")
_DataT = TypeVar("_DataT", bound=Data)


class Configurable(ABC, Generic[_DataT]):
    """
    Any configurable object.
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


class ConfigurationDependentSelfFactory(Configurable[_DataT], ABC):
    """
    Create factories that require configuration.
    """

    @classmethod
    @abstractmethod
    def new_for_configuration(cls, configuration: _DataT) -> ServiceLevelTarget[Self]:
        """
        Create a new factory for the given configuration.
        """


class _HumanFacingFactoryError(FactoryError, HumanFacingException):
    pass


def new_target(
    target: ConfigurationDependentSelfFactory[Data] | ServiceLevelTarget[_T],
    configuration: Data | PortableData | Void = Void(),  # noqa: B008
    /,
) -> ServiceLevelTarget[_T]:
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
        if isinstance(configuration, Data):
            if not isinstance(configuration, target.configuration_cls()):
                raise FactoryError(
                    f"{fully_qualified_name(target)} required {fully_qualified_name(target.configuration_cls())}, but {fully_qualified_name(type(configuration))} was given."
                )
        else:
            configuration_cls = cast(
                type[ConfigurationDependentSelfFactory], target
            ).configuration_cls()
            if issubclass(configuration_cls, Data):
                configuration = configuration_cls.data().porter.load(configuration)
            else:
                configuration = configuration_cls.load(configuration)
        return target.new_for_configuration(configuration)  # ty:ignore[invalid-return-type, invalid-argument-type]
    return target  # ty:ignore[invalid-return-type]
