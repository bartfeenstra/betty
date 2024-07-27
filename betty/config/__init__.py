"""
The Configuration API.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from contextlib import chdir
from typing import (
    Generic,
    TypeVar,
    Any,
    Self,
    TypeAlias,
    TYPE_CHECKING,
)

import aiofiles
from aiofiles.os import makedirs

from betty.assertion import (
    AssertionChain,
    assert_file_path,
)
from betty.assertion.error import AssertionFailedGroup
from betty.locale.localizable import static
from betty.serde.dump import Dumpable, Dump
from betty.serde.format import FormatRepository

if TYPE_CHECKING:
    from pathlib import Path


_ConfigurationListener: TypeAlias = Callable[[], None]
ConfigurationListener: TypeAlias = "Configuration | _ConfigurationListener"


class Configuration(Dumpable):
    """
    Any configuration object.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

    @abstractmethod
    def update(self, other: Self) -> None:
        """
        Update this configuration with the values from ``other``.
        """
        pass

    @abstractmethod
    def load(self, dump: Dump) -> None:
        """
        Load dumped configuration.

        :raises betty.assertion.error.AssertionFailed: Raised if the dump contains invalid configuration.
        """
        pass


_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class Configurable(Generic[_ConfigurationT]):
    """
    Any configurable object.
    """

    _configuration: _ConfigurationT

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

    @property
    def configuration(self) -> _ConfigurationT:
        """
        The object's configuration.
        """
        if not hasattr(self, "_configuration"):
            raise RuntimeError(
                f"{self} has no configuration. {type(self)}.__init__() must ensure it is set."
            )
        return self._configuration


def assert_configuration_file(
    configuration: _ConfigurationT,
) -> AssertionChain[Path, _ConfigurationT]:
    """
    Assert that configuration can be loaded from a file.
    """

    def _assert(configuration_file_path: Path) -> _ConfigurationT:
        formats = FormatRepository()
        with (
            AssertionFailedGroup().assert_valid() as errors,
            # Change the working directory to allow relative paths to be resolved
            # against the configuration file's directory path.
            chdir(configuration_file_path.parent),
        ):
            with open(configuration_file_path) as f:
                read_configuration = f.read()
            with errors.catch(static(f"in {str(configuration_file_path.resolve())}")):
                configuration.load(
                    formats.format_for(configuration_file_path.suffix[1:]).load(
                        read_configuration
                    )
                )
            return configuration

    return assert_file_path() | _assert


async def write_configuration_file(
    configuration: Configuration, configuration_file_path: Path
) -> None:
    """
    Write configuration to file.
    """
    formats = FormatRepository()
    dump = formats.format_for(configuration_file_path.suffix[1:]).dump(
        configuration.dump()
    )
    await makedirs(configuration_file_path.parent, exist_ok=True)
    async with aiofiles.open(configuration_file_path, mode="w") as f:
        await f.write(dump)
