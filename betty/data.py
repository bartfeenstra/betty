"""
Describe, access, and manipulate arbitrary data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final

from betty.definition import HasDefinition
from betty.definition.cls import OptionalClsDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.functools import LazyReCallable
from betty.portable import Porter
from betty.portable.error import NotPortable
from betty.sample import Samples

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.localizable import ResolvableLocalizable


type ResolvableDataPorter[DefinitionT: DataDefinition, DataT] = (
    Porter[DataT] | Callable[[DefinitionT], Porter[DataT]]
)


type ResolvableDataSamples[DefinitionT: DataDefinition, DataT] = (
    Samples[DataT] | Callable[[DefinitionT], Samples[DataT]]
)


class DataDefinition[DataT](HumanFacingDefinition, OptionalClsDefinition[DataT]):
    """
    A data definition.
    """

    def __init__(
        self,
        *args: Any,
        cls: type[DataT] | None = None,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        porter: ResolvableDataPorter[Self, DataT] | None = None,
        samples: ResolvableDataSamples[Self, DataT] | None = None,
        **kwargs: Any,
    ):
        self.__samples = samples or Samples()
        self.__porter = LazyReCallable[Porter[DataT]](
            lambda: (
                porter(self) if porter and not isinstance(porter, Porter) else porter
            )  # ty:ignore[invalid-argument-type]
        )
        super().__init__(*args, cls=cls, label=label, description=description, **kwargs)

    @final
    @property
    def porter(self) -> Porter[DataT]:
        """
        The porter for the data.
        """
        if not (porter := self.try_porter):
            raise NotPortable(f"{self!r} does not have a porter.")
        return porter

    @final
    @property
    def try_porter(self) -> Porter[DataT] | None:
        """
        The porter for the data, if it has one.
        """
        return self.__porter()

    @final
    @property
    def samples(self) -> Samples:
        """
        Any samples for this data.
        """
        if isinstance(self.__samples, Samples):
            return self.__samples
        return self.__samples(self)


class Data[DefinitionT: DataDefinition = DataDefinition](HasDefinition[DefinitionT]):
    """
    A class that defines data for its instances.
    """

    __slots__ = ()

    def __eq__(self, other: object, /) -> bool:
        if self is other:
            return True
        if type(self) is not type(other):
            return NotImplemented
        porter = self.definition.try_porter
        if porter is None:
            return NotImplemented
        return porter.dump(self) == porter.dump(other)


type ResolvableDataDefinition[DefinitionT: DataDefinition = DataDefinition] = (
    DefinitionT | type[Data[DefinitionT]]
)


def resolve_data_definition[DefinitionT: DataDefinition](
    definition: ResolvableDataDefinition[DefinitionT],
) -> DefinitionT:
    """
    Resolve a value to a data definition.
    """
    if isinstance(definition, DataDefinition):
        return definition
    return definition.definition
