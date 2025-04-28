"""
The Configuration API.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from contextlib import chdir
from typing import TYPE_CHECKING, Any, Generic, Self, TypeAlias, TypeVar

import aiofiles
from aiofiles.os import makedirs

from betty.assertion import AssertionChain, assert_file_path
from betty.assertion.error import AssertionFailedGroup
from betty.locale.localizable import plain
from betty.mutability import Mutable
from betty.serde.dump import Dumpable
from betty.serde.format import FORMAT_REPOSITORY, format_for
from betty.serde.load import Loadable

if TYPE_CHECKING:
    from pathlib import Path


_ConfigurationListener: TypeAlias = Callable[[], None]
ConfigurationListener: TypeAlias = "Configuration | _ConfigurationListener"


class Configuration(Mutable, Loadable, Dumpable):
    """
    Any configuration object.
    """

    def update(self, other: Self) -> None:
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


class DefaultConfigurable(Configurable[_ConfigurationT], Generic[_ConfigurationT]):
    """
    A configurable type that can provide its own default configuration.
    """

    @classmethod
    @abstractmethod
    def new_default_configuration(cls) -> _ConfigurationT:
        """
        Create this extension's default configuration.
        """


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
