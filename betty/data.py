"""
Describe, access, and manipulate arbitrary data.
"""

from __future__ import annotations

from inspect import signature
from typing import TYPE_CHECKING, Any, Final, Self, final, override

from betty.definition.cls import OptionalClsDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.importlib import fully_qualified_name
from betty.portable import Porter
from betty.portable.error import NotPortable
from betty.sample import Samplable, Sample, Samples

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, MutableMapping

    from betty.localizable import ResolvableLocalizable
    from betty.typing import Intersection

type DataDefinitionFeatureManufacturer[
    ManufacturableT,
    DataDefinitionT: DataDefinition,
    DataT,
] = (
    Callable[[DataDefinitionT], ManufacturableT]
    | Callable[[DataDefinitionT, type[DataT]], ManufacturableT]
)

type ResolvableDataDefinitionFeature[
    ManufacturableT,
    DataDefinitionT: DataDefinition,
    DataT,
] = (
    ManufacturableT
    | DataDefinitionFeatureManufacturer[ManufacturableT, DataDefinitionT, DataT]
)


class DataDefinition[DataT, PorterT: Porter = Porter](
    HumanFacingDefinition, OptionalClsDefinition[DataT]
):
    """
    A data definition.
    """

    def __init__(
        self,
        *args: Any,
        cls: type[DataT] | None = None,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        porter: ResolvableDataDefinitionFeature[
            Intersection[PorterT, Porter[DataT]], Self, DataT
        ]
        | None = None,
        samples: Iterable[
            Callable[[], Sample[DataT]]
            | Samples[DataT]
            | type[Intersection[DataT, Samplable]]
        ] = (),
        **kwargs: Any,
    ):
        self._samples = tuple(samples)
        self._porter: Intersection[PorterT, Porter[DataT]] | None = None
        self._porter_set_cls_factory: (
            Callable[[Self, type[DataT]], Intersection[PorterT, Porter[DataT]]] | None
        ) = None
        factory_signature: int | None = None
        if porter is not None:
            if isinstance(porter, Porter):
                self._porter = porter
            else:
                factory_signature = len(signature(porter).parameters)
                if factory_signature == 2:
                    self._porter_set_cls_factory = porter  # ty:ignore[invalid-assignment]
        super().__init__(*args, cls=cls, label=label, description=description, **kwargs)
        if factory_signature == 1:
            self._porter = porter(self)  # ty:ignore[call-non-callable, missing-argument]

    @final
    @property
    def porter(self) -> Intersection[PorterT, Porter[DataT]]:
        """
        The porter for the data.

        :raises betty.portable.error.NotPortable:
        """
        if not self._porter:
            raise NotPortable("This data does not have a porter.")
        return self._porter

    @final
    @property
    def try_porter(self) -> Intersection[PorterT, Porter[DataT]] | None:
        """
        The porter for the data, if it has one.
        """
        return self._porter

    @override
    def _set_cls(self, cls: type[DataT], /) -> None:
        super()._set_cls(cls)
        if issubclass(cls, Data):
            assert cls not in _datas, (
                f"Found an existing data definition {_datas[cls]} when adding {self} for {cls}"
            )
            _datas[cls] = self
        if self._porter_set_cls_factory:
            self._porter = self._porter_set_cls_factory(self, cls)

    @final
    @property
    def samples(self) -> Samples:
        """
        Any samples for this data.
        """
        if not self._samples:
            if self.cls and issubclass(self.cls, Samplable):
                return Samples([self.cls])
            return Samples(())
        return Samples(self._samples)


_datas: Final[MutableMapping[type, DataDefinition]] = {}


class Data[DataDefinitionT: DataDefinition = DataDefinition]:
    """
    A class that defines data for its instances.
    """

    @final
    @classmethod
    def data(cls) -> Intersection[DataDefinitionT, DataDefinition[Self]]:
        """
        Define the data for instances of this class.
        """
        try:
            return _datas[cls]
        except KeyError:
            raise NotImplementedError(
                f"{fully_qualified_name(cls)} was not decorated with {fully_qualified_name(DataDefinition)} or any subclass."
            ) from None

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if type(self) is not type(other):
            return NotImplemented
        porter = type(self).data().porter
        if porter is None:
            return NotImplemented
        return porter.dump(self) == porter.dump(other)


type ResolvableDataDefinition[DataDefinitionT: DataDefinition = DataDefinition] = (
    DataDefinitionT | type[Data[DataDefinitionT]]
)


def resolve_data_definition[DataDefinitionT: DataDefinition](
    definition: ResolvableDataDefinition[DataDefinitionT],
) -> DataDefinitionT:
    """
    Resolve a value to a data definition.
    """
    if isinstance(definition, DataDefinition):
        return definition  # ty:ignore[invalid-return-type]
    return definition.data()
