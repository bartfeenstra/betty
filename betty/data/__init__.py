"""
Describe, access, and manipulate arbitrary data.
"""

from __future__ import annotations

from functools import update_wrapper
from typing import TYPE_CHECKING, Any, Generic, Self, final

from typing_extensions import TypeVar, override

from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.importlib import fully_qualified_name
from betty.portable import OptionalPorter, Portable, PortablePorter, Porter
from betty.portable.error import NotPortable
from betty.sample import Sample, Samples, Size
from betty.service.hydrate import Hydratable, Hydrator

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from ty_extensions import Intersection

    from betty.locale.localizable import ResolvableLocalizable
    from betty.service.level import ServiceLevel

_DataClsT = TypeVar("_DataClsT", default=Any)


class DataDefinition(
    HumanFacingDefinition, ClsDefinition[_DataClsT], Hydrator[_DataClsT]
):
    """
    A data definition.
    """

    def __init__(
        self,
        *,
        cls: type[_DataClsT] | None = None,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        porter: Porter[_DataClsT] | None = None,
        samples: Iterable[Callable[[], Sample[_DataClsT]] | Samples] | None = None,
    ):
        super().__init__(cls=cls, label=label, description=description)
        self._porter = porter
        self._samples = Samples(() if samples is None else samples)

    @property
    def porter(self) -> Porter[_DataClsT]:
        """
        The porter for the data.
        """
        if self._porter is None:
            if not issubclass(self.cls, Portable):
                raise NotPortable(
                    f"This definition does not have a porter. Either make the data class {fully_qualified_name(self.cls)} subclass {fully_qualified_name(Portable)}, or provide a porter when initializing the definition."
                )
            self._porter = PortablePorter(self.cls)
        return self._porter

    @override
    def _set_cls(self, cls: type[_DataClsT]) -> None:
        super()._set_cls(cls)
        if issubclass(cls, Data):
            cls.data = staticmethod(update_wrapper(lambda: self, cls.data))  # ty:ignore[invalid-assignment]

    @property
    def samples(self) -> Samples:
        """
        Any samples for this data.
        """
        return self._samples

    @override
    async def hydrate(self, *, services: ServiceLevel, data: _DataClsT) -> None:
        if isinstance(data, Hydratable):
            await data.hydrate(services=services)


_DataDefinitionT = TypeVar(
    "_DataDefinitionT", bound=DataDefinition, default=DataDefinition, covariant=True
)


class Data(Generic[_DataDefinitionT]):
    """
    A class that defines data for its instances.
    """

    @classmethod
    def data(cls) -> Intersection[_DataDefinitionT, DataDefinition[Self]]:
        """
        Define the data for instances of this class.
        """
        raise NotImplementedError(
            f"{fully_qualified_name(cls)} was not decorated with {fully_qualified_name(DataDefinition)} or any subclass."
        )

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        porter = type(self).data().porter
        return porter.dump(self) == porter.dump(other)


@final
class OptionalDefinition(DataDefinition[_DataClsT | None]):
    """
    Wrap another data definition to make it optional, e.g. allow ``None``.
    """

    def __init__(self, wrapped: DataDefinition[_DataClsT], /):
        super().__init__(
            cls=wrapped.cls,
            label=wrapped.label,
            description=wrapped.description,
            porter=OptionalPorter(wrapped.porter),  # ty:ignore[invalid-argument-type]
            samples=[
                lambda: Sample(None, label="Minimal", size=Size.MINIMAL),
                wrapped.samples,
            ],
        )
        self._wrapped = wrapped

    @property
    def wrapped(self) -> DataDefinition[_DataClsT]:
        """
        The wrapped, required (non-optional) data definition.
        """
        return self._wrapped

    @override
    async def hydrate(self, *, services: ServiceLevel, data: _DataClsT | None) -> None:
        if data is not None:
            await self.wrapped.hydrate(services=services, data=data)
