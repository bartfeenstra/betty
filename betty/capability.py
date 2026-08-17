"""
The capability API.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping
from typing import Any, Final, Never, Self, final

from betty.collections import _empty_frozen_mapping
from betty.importlib import fully_qualified_name
from betty.nothing import Nothing
from betty.typing import Intersection

type CapabilityManufacturer[OwnerT, ManufacturableT] = Callable[
    [OwnerT], ManufacturableT
]

type ResolvableCapability[OwnerT, ManufacturableT] = (
    ManufacturableT | CapabilityManufacturer[OwnerT, ManufacturableT]
)


class Stage[OwnerT, ManufacturableT]:
    """
    A capability factory stage.
    """

    @final
    def __init__(
        self, manufacturer: CapabilityManufacturer[OwnerT, ManufacturableT], /
    ):
        self.manufacturer: Final[CapabilityManufacturer[OwnerT, ManufacturableT]] = (
            manufacturer
        )
        """
        The capability manufacturer.
        """


type StagedCapabilityManufacturer[OwnerT, ManufacturableT, StageT: Stage = Never] = (
    Intersection[StageT, Stage[OwnerT, ManufacturableT]]
)

type ResolvableStagedCapability[OwnerT, ManufacturableT, StageT: Stage = Never] = (
    ManufacturableT
    | CapabilityManufacturer[OwnerT, ManufacturableT]
    | StagedCapabilityManufacturer[OwnerT, ManufacturableT, StageT]
)


class CapabilityError(RuntimeError):
    """
    Raised for errors related to capabilities.
    """


@final
class UnsupportedCapability(CapabilityError):
    """
    Raised when an object does not support the requested capability.
    """

    def __init__(self, owner: Capable, capability: str, /):
        super().__init__(
            f'{fully_qualified_name(type(owner))} does not support the "{capability}" capability.'
        )


@final
class Incapable(CapabilityError):
    """
    Raised when an object does not have the requested capability.
    """

    def __init__(self, owner: Capable, capability: str, /):
        super().__init__(
            f'{fully_qualified_name(type(owner))} does not have a(n) "{capability}" capability.'
        )


@final
class NotYetInitialized(CapabilityError):
    """
    Raised when an object's capability has not been initialized.
    """

    def __init__(self, owner: Capable, capability: str, stage: type[Stage], /):
        super().__init__(
            f'{fully_qualified_name(type(owner))}\'s "{capability}" capability was not yet initialized for stage {fully_qualified_name(stage)}.'
        )


class Capable[StageT: Stage = Never]:
    """
    An object that can be extended with arbitrary capabilities.
    """

    def __init__(
        self,
        *args: Any,
        capabilities: Mapping[
            str, tuple[type, ResolvableStagedCapability[Self, Any, StageT]]
        ] = _empty_frozen_mapping,
        **kwargs: Any,
    ):
        self._capabilities: Final[
            MutableMapping[str, ResolvableStagedCapability[Self, Any, StageT]]
        ] = {}
        super().__init__(*args, **kwargs)
        if capabilities is not None:
            for capability_name, (
                capability_type,
                capability_value,
            ) in capabilities.items():
                if capability_value is None or isinstance(
                    capability_value, (capability_type, Stage)
                ):
                    self._capabilities[capability_name] = capability_value
                else:
                    self._capabilities[capability_name] = capability_value(self)  # ty:ignore[call-non-callable]

    @final
    def _init_staged_capabilities(self, stage: type[StageT], /) -> None:
        for capability_name, capability_value in self._capabilities.items():
            if isinstance(capability_value, stage):
                self._capabilities[capability_name] = capability_value.manufacturer(
                    self
                )

    @final
    def _capability(self, name: str, /) -> Any:
        """
        Get a capability.

        :raises betty.capability.CapabilityError:
        """
        capability = self._try_capability(name)
        if capability is None:
            raise Incapable(self, name)
        return capability

    @final
    def _try_capability(self, name: str, /) -> Any | None:
        """
        Try to get a capability, or return ``None`` if it does not exist.
        """
        capability = self._capabilities.get(name, Nothing)
        if capability is Nothing:
            raise UnsupportedCapability(self, name)
        if isinstance(capability, Stage):
            raise NotYetInitialized(self, name, type(capability))
        return capability


class HasCapabilities[StageT: Stage = Never](Capable[StageT]):
    """
    An object that exposes its capabilities.
    """

    @final
    def capability(self, name: str, /) -> Any:
        """
        Get a capability.

        :raises betty.capability.CapabilityError:
        """
        return self._capability(name)

    @final
    def try_capability(self, name: str, /) -> Any | None:
        """
        Try to get a capability, or return ``None`` if it does not exist.
        """
        return self._try_capability(name)
