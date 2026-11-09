"""
Describe, access, and manipulate arbitrary data.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Self, final, override

from wrapt import BaseObjectProxy

from betty.classtools import TypeABCMeta
from betty.definition import HasDefinition
from betty.definition.cls import OptionalClsDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.functools import LazyReCallable
from betty.portable import PortableData, Porter
from betty.porters.optional import OptionalPorter
from betty.sample import Sample, Samples, Size

if TYPE_CHECKING:
    from collections.abc import Callable

    from ty_extensions import Intersection

    from betty.localizer import AnyLocalizable


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
        label: AnyLocalizable,
        description: AnyLocalizable | None = None,
        samples: ResolvableDataSamples[Self, DataT] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, cls=cls, label=label, description=description, **kwargs)
        self.__samples = samples or Samples()

    @final
    def default(
        self, default: DataT, /
    ) -> Intersection[Self, DefaultDataDefinition[DataT]]:
        """
        Create a new definition like this one, but with the given default data.
        """
        return _DefaultDataDefinitionProxy(  # ty:ignore[invalid-return-type]
            self,
            default,
        )

    @final
    def new_default(
        self, default: Callable[[Self], DataT], /
    ) -> Intersection[Self, DefaultDataDefinition[DataT]]:
        """
        Create a new definition like this one, but with the given default data factory.
        """
        return _NewDefaultDataDefinitionProxy(  # ty:ignore[invalid-return-type]
            self,
            default,
        )

    @final
    @property
    def optional(self) -> Intersection[Self, DefaultDataDefinition[DataT | None]]:
        """
        Create a new definition like this one, but where the data may also be ``None``.
        """
        return _OptionalDataDefinitionProxy(  # ty:ignore[invalid-return-type]
            self,
        )

    @final
    def portable[PortableDataT: PortableData](
        self, porter: ResolvableDataPorter[DataT, PortableDataT], /
    ) -> PortableDataDefinition[DataT, PortableDataT]:
        """
        Create a new definition like this one, but with the given porter.
        """
        return _PortableDataDefinitionProxy(  # ty:ignore[invalid-return-type]
            self,
            porter,
        )

    # @todo Remove this
    @property
    def porter(self) -> Porter[DataT]:
        """
        The porter for the data.
        """
        raise NotImplementedError

    @final
    def samplable(self, samples: ResolvableDataSamples[Self, DataT], /) -> Self:
        """Create a new definition like this one, but with the added samples."""
        # @todo
        return self
        # raise NotImplementedError

    @final
    @property
    def samples(self) -> Samples:
        """
        Any samples for this data.
        """
        if isinstance(self.__samples, Samples):
            return self.__samples
        return self.__samples(self)


class DefaultDataDefinition[DataT](DataDefinition[DataT], metaclass=TypeABCMeta):
    """
    A data definition that can produce default values.
    """

    @abstractmethod
    def new(self) -> DataT:
        """
        Create new default data.
        """


# @todo assert issubclass(_DefaultDataDefinitionProxy, DefaultDataDefinition) is True
@final
class _DefaultDataDefinitionProxy[DefinitionT: DataDefinition, DataT](
    DefaultDataDefinition[DataT], BaseObjectProxy[DefinitionT]
):
    def __init__(self, wrapped: DefinitionT, default: DataT, /):
        super().__init__(
            wrapped,
            # @todo Remove the dummy label
            label="",
        )
        self._default = default

    @override
    def new(self) -> DataT:
        return self._default


# @todo assert issubclass(_NewDefaultDataDefinitionProxy, DefaultDataDefinition) is True
@final
class _NewDefaultDataDefinitionProxy[DefinitionT: DataDefinition, DataT](
    DefaultDataDefinition[DataT], BaseObjectProxy[DefinitionT]
):
    def __init__(
        self, wrapped: DefinitionT, default: Callable[[DefinitionT], DataT], /
    ):
        super().__init__(wrapped)
        self._default = default

    @override
    def new(self) -> DataT:
        return self._default(self)


# @todo assert issubclass(_OptionalDataDefinitionProxy, OptionalDataDefinition) is True
@final
class _OptionalDataDefinitionProxy[DefinitionT: DataDefinition, DataT](
    DataDefinition[DataT], BaseObjectProxy[DefinitionT]
):
    def __init__(self, wrapped: DefinitionT, /):
        if isinstance(wrapped, PortableDataDefinition):
            wrapped = wrapped.portable(OptionalPorter(wrapped.porter))
        super().__init__(
            wrapped.default(None).samplable(
                Samples(
                    lambda: Sample(None, label="Minimal", size=Size.MINIMAL),
                    wrapped.samples,
                )
            ),
            # @todo Remove the dummy label
            label="",
        )


class PortableDataDefinition[DataT, PortableDataT: PortableData = PortableData](
    DataDefinition[DataT], metaclass=TypeABCMeta
):
    """
    A data definition that allows the data to be loaded from and dumped to portable data.
    """

    @property
    @abstractmethod
    def porter(self) -> Porter[DataT, PortableDataT]:
        """
        The porter for the data.
        """


class PortableDataDefinitionBase[DataT, PortableDataT: PortableData = PortableData](
    PortableDataDefinition[DataT]
):
    """
    A base class to make any data definition portable.
    """

    def __init__(
        self,
        *args: Any,
        porter: ResolvableDataPorter[DataT, PortableDataT],
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.__porter = LazyReCallable[Porter[DataT, PortableDataT]](
            lambda: porter if isinstance(porter, Porter) else porter(self)  # ty:ignore[invalid-argument-type]
        )

    @final
    @override
    @property
    def porter(self) -> Porter[DataT, PortableDataT]:
        return self.__porter()


# @todo assert issubclass(_PortableDataDefinitionProxy, PortableDataDefinition) is True
@final
class _PortableDataDefinitionProxy[
    DefinitionT: DataDefinition,
    DataT,
    PortableDataT: PortableData,
](PortableDataDefinitionBase[DataT], BaseObjectProxy[DefinitionT]):
    def __init__(
        self,
        wrapped: DefinitionT,
        porter: ResolvableDataPorter[DataT, PortableDataT],
        /,
    ):
        super().__init__(
            wrapped,
            porter=porter,
            # @todo Remove the dummy label
            label="",
        )


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
        if isinstance(self, PortableDataDefinition):
            porter = self.definition.porter
            return porter.dump(self) == porter.dump(other)
        return NotImplemented


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
