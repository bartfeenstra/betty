"""
The Configuration API.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from contextlib import chdir
from typing import Generic, TypeVar, Self, TypeAlias, TYPE_CHECKING

import aiofiles
from aiofiles.os import makedirs

from betty.assertion import AssertionChain, assert_file_path
from betty.assertion.error import AssertionFailedGroup
from betty.locale.localizable import plain
from betty.serde.dump import Dumpable
from betty.serde.format import FORMAT_REPOSITORY, format_for
from betty.serde.load import Loadable

if TYPE_CHECKING:
    from pathlib import Path


_ConfigurationListener: TypeAlias = Callable[[], None]
ConfigurationListener: TypeAlias = "Configuration | _ConfigurationListener"


class Configuration(Loadable, Dumpable):
    """
    Any configuration object.
    """

    @abstractmethod
    def update(self, other: Self) -> None:
        """
        Update this configuration with the values from ``other``.
        """
        pass


_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class Configurable(Generic[_ConfigurationT]):
    """
    Any configurable object.
    """

    _configuration: _ConfigurationT

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


async def assert_configuration_file(
    configuration: _ConfigurationT,
) -> AssertionChain[Path, _ConfigurationT]:
    """
    Assert that configuration can be loaded from a file.
    """
    available_formats = {
        available_format: await FORMAT_REPOSITORY.new_target(available_format)
        async for available_format in FORMAT_REPOSITORY
    }

    def _assert(configuration_file_path: Path) -> _ConfigurationT:
        with (
            AssertionFailedGroup().assert_valid() as errors,
            # Change the working directory to allow relative paths to be resolved
            # against the configuration file's directory path.
            chdir(configuration_file_path.parent),
        ):
            with open(configuration_file_path) as f:
                read_configuration = f.read()
            with errors.catch(plain(f"in {str(configuration_file_path.resolve())}")):
                configuration_file_format = available_formats[
                    format_for(list(available_formats), configuration_file_path.suffix)
                ]
                configuration.load(configuration_file_format.load(read_configuration))
            return configuration

    return assert_file_path() | _assert


async def write_configuration_file(
    configuration: Configuration, configuration_file_path: Path
) -> None:
    """
    Write configuration to file.
    """
    serde_format_type = format_for(
        await FORMAT_REPOSITORY.select(), configuration_file_path.suffix
    )
    serde_format = await FORMAT_REPOSITORY.new_target(serde_format_type)
    dump = serde_format.dump(configuration.dump())
    await makedirs(configuration_file_path.parent, exist_ok=True)
    async with aiofiles.open(configuration_file_path, mode="w") as f:
        await f.write(dump)
