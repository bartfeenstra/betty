"""
Describe, access, and manipulate arbitrary data.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Self, final, override

from wrapt import BaseObjectProxy

from betty.definition import HasDefinition
from betty.definition.cls import OptionalClsDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.functools import LazyReCallable
from betty.portable import Porter
from betty.porters.optional import OptionalPorter
from betty.sample import ResolvableSamples, Sample, Samples, Size

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from ty_extensions import Intersection

    from betty.localizer import AnyLocalizable


type ResolvableDataPorter[
    DefinitionT: DataDefinition,
    DataT,
    PorterT: Porter = Porter,
] = (
    Intersection[PorterT, Porter[DataT]]
    | Callable[[DefinitionT], Intersection[PorterT, Porter[DataT]]]
)


type ResolvableDataSamples[DefinitionT: DataDefinition, DataT] = (
    ResolvableSamples[DataT] | Callable[[DefinitionT], Samples[DataT]]
)


def _resolve_data_samples[DefinitionT: DataDefinition, DataT](
    definition: Intersection[DefinitionT, DataDefinition[DataT]],
    *samples: ResolvableDataSamples[DefinitionT, DataT],
) -> Iterator[Sample[DataT]]:
    for sample in samples:
        if isinstance(sample, Samples | tuple | Sample):
            yield from Samples(sample)
        else:
            yield from sample(definition)


# @todo Extract implementations to DataDefinitionBase? That would solve our proxy issues straight away.
# @todo
# @todo Except that we would have to do that for every, single, Definition base class
# @todo
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
        self.__samples = () if samples is None else samples

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
    def portable[PorterT: Porter](
        self, porter: ResolvableDataPorter[Self, DataT, PorterT], /
    ) -> Intersection[Self, PortableDataDefinition[DataT, PorterT]]:
        """
        Create a new definition like this one, but with the given porter.
        """
        return _PortableDataDefinitionProxy(  # ty:ignore[invalid-return-type]
            self,
            porter,
        )

    @final
    def samplable(self, samples: ResolvableDataSamples[Self, DataT], /) -> Self:
        """Create a new definition like this one, but with the added samples."""
        return _SamplableDataDefinition(  # ty:ignore[invalid-return-type]
            self,
            samples,
        )

    @final
    @property
    def samples(self) -> Samples:
        """
        Any samples for this data.
        """
        return Samples(*_resolve_data_samples(self, self.__samples))


class DefaultDataDefinition[DataT](DataDefinition[DataT], metaclass=ABCMeta):
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
    BaseObjectProxy[DefinitionT], DefaultDataDefinition[DataT]
):
    def __init__(self, wrapped: DefinitionT, default: DataT, /):
        BaseObjectProxy.__init__(self, wrapped)
        DefaultDataDefinition.__init__(
            self,
            cls=wrapped.cls,
            label=wrapped.label,
            description=wrapped.description,
            samples=wrapped.samples,
        )
        self._default = default

    @override
    def new(self) -> DataT:
        return self._default


# @todo assert issubclass(_NewDefaultDataDefinitionProxy, DefaultDataDefinition) is True
@final
class _NewDefaultDataDefinitionProxy[DefinitionT: DataDefinition, DataT](
    BaseObjectProxy[DefinitionT], DefaultDataDefinition[DataT]
):
    def __init__(
        self, wrapped: DefinitionT, default: Callable[[DefinitionT], DataT], /
    ):
        BaseObjectProxy.__init__(self, wrapped)
        DefaultDataDefinition.__init__(
            self,
            cls=wrapped.cls,
            label=wrapped.label,
            description=wrapped.description,
            samples=wrapped.samples,
        )
        self._default = default

    @override
    def new(self) -> DataT:
        return self._default(self.__wrapped__)


# @todo assert issubclass(_OptionalDataDefinitionProxy, OptionalDataDefinition) is True
@final
class _OptionalDataDefinitionProxy[DefinitionT: DataDefinition, DataT](
    BaseObjectProxy[DefinitionT], DataDefinition[DataT | None]
):
    def __init__(self, wrapped: DefinitionT, /):
        if isinstance(wrapped, PortableDataDefinition):
            wrapped = wrapped.portable(OptionalPorter(wrapped.porter))
        BaseObjectProxy.__init__(
            self,
            # @todo We can't set a default on `wrapped` because we don't know if None is supported!
            # @todo Find another way.
            # @todo
            # @todo Maybe subclass _DefaultDataDefinitionProxy here?
            # @todo
            wrapped.default(None),
        )
        DataDefinition.__init__(
            self,
            cls=wrapped.cls,
            label=wrapped.label,
            description=wrapped.description,
            samples=Samples(
                Sample(lambda: None, label="Minimal", size=Size.MINIMAL),
                wrapped.samples,
            ),
        )


class PortableDataDefinition[DataT, PorterT: Porter = Porter](
    DataDefinition[DataT], metaclass=ABCMeta
):
    """
    A data definition that allows the data to be loaded from and dumped to portable data.
    """

    @property
    @abstractmethod
    def porter(self) -> Intersection[PorterT, Porter[DataT]]:
        """
        The porter for the data.
        """


class PortableDataDefinitionBase[DataT, PorterT: Porter = Porter](
    PortableDataDefinition[DataT, PorterT]
):
    """
    A base class to make any data definition portable.
    """

    def __init__(
        self,
        *args: Any,
        porter: ResolvableDataPorter[
            PortableDataDefinition[DataT, PorterT],
            DataT,
            Intersection[PorterT, Porter[DataT]],
        ],
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.__porter = LazyReCallable[PorterT](
            lambda: porter if isinstance(porter, Porter) else porter(self)  # ty:ignore[invalid-argument-type]
        )

    @final
    @override
    @property
    def porter(self) -> PorterT:
        return self.__porter()


# @todo assert issubclass(_PortableDataDefinitionProxy, PortableDataDefinition) is True
@final
class _PortableDataDefinitionProxy[DefinitionT: DataDefinition, DataT, PorterT: Porter](
    BaseObjectProxy[DefinitionT], PortableDataDefinitionBase[DataT, PorterT]
):
    def __init__(
        self,
        wrapped: DefinitionT,
        porter: ResolvableDataPorter[DefinitionT, DataT, PorterT],
        /,
    ):
        BaseObjectProxy.__init__(self, wrapped)
        PortableDataDefinitionBase.__init__(
            self,
            porter=porter,  # ty: ignore[invalid-argument-type]
            cls=wrapped.cls,
            label=wrapped.label,
            description=wrapped.description,
            samples=wrapped.samples,
        )


# @todo assert issubclass(_SamplableDataDefinition, Samplable) is True
@final
class _SamplableDataDefinition[DefinitionT: DataDefinition, DataT](
    BaseObjectProxy[DefinitionT], DataDefinition[DataT]
):
    def __init__(
        self,
        wrapped: DefinitionT,
        samples: ResolvableDataSamples[DefinitionT, DataT],
        /,
    ):
        BaseObjectProxy.__init__(self, wrapped)
        DataDefinition.__init__(
            self,
            cls=wrapped.cls,
            label=wrapped.label,
            description=wrapped.description,
            samples=(*_resolve_data_samples(wrapped, samples, wrapped.samples),),
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
