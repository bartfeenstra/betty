"""
The Configuration API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, Self

from typing_extensions import TypeVar, override

from betty.locale.localizable.ensure import ensure_localizable
from betty.portable import Portable, PortableData

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.locale.localizable import Localizable, LocalizableLike
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
    def samples(cls) -> Iterable[Sample[Self]]:  # type: ignore[type-var]
        """
        Create samples for this configuration.
        """
        return ()


_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration, default=Configuration)


class Sample(Generic[_ConfigurationT]):
    """
    A configuration sample.

    Samples are useful for generating documentation and tests.
    """

    def __init__(
        self,
        configuration: _ConfigurationT,
        *,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
        minimal: bool = False,
        full: bool = False,
    ):
        self._configuration = configuration
        self._label = ensure_localizable(label)
        self._description = ensure_localizable(description) if description else None
        self._minimal = minimal
        self._full = full

    @property
    def configuration(self) -> _ConfigurationT:
        """
        The sample configuration.
        """
        return self._configuration

    @property
    def label(self) -> Localizable:
        """
        The sample's human-readable short label.
        """
        return self._label

    @property
    def description(self) -> Localizable | None:
        """
        The sample's human-readable long description.
        """
        return self._description

    @property
    def minimal(self) -> bool:
        """
        Whether this is a minimal sample.
        """
        return self._minimal

    @property
    def full(self) -> bool:
        """
        Whether this is a full sample.
        """
        return self._full


def get_minimal_sample(configuration: type[_ConfigurationT]) -> Sample[_ConfigurationT]:
    """
    Get a sample for a configuration type, preferably as minimal as possible.
    """
    samples = list(configuration.samples())
    for sample in samples:
        if sample.minimal:
            return sample
    for sample in samples:
        if not sample.full:
            return sample
    return samples[0]


def get_full_sample(configuration: type[_ConfigurationT]) -> Sample[_ConfigurationT]:
    """
    Get a sample for a configuration type, preferably as full as possible.
    """
    samples = list(configuration.samples())
    for sample in samples:
        if sample.full:
            return sample
    for sample in samples:
        if not sample.minimal:
            return sample
    return samples[0]


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
