"""
The Configuration API.
"""

from __future__ import annotations

from typing import Any, Generic, Self, TypeVar

from betty.mutability import Mutable
from betty.serde.dump import Dumpable
from betty.serde.load import Loadable


class Configuration(Mutable, Loadable, Dumpable):
    """
    Any configuration object.
    """

    def update(self, other: Self, /) -> None:
        """
        Update this configuration with the values from ``other``.
        """
        self.assert_mutable()
        self.load(other.dump())


_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class Configurable(Generic[_ConfigurationT]):
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
