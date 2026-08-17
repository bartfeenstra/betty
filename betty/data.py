"""
Describe, access, and manipulate arbitrary data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, Self, final, override

from betty.collections import _empty_frozen_mapping
from betty.definition.cls import ClsDefinitionCapabilityStage, OptionalClsDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.importlib import fully_qualified_name
from betty.portable import Porter
from betty.sample import Samplable, Sample, Samples
from betty.search import Indexer

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, MutableMapping

    from betty.capability import ResolvableStagedCapability, Stage
    from betty.localizable import ResolvableLocalizable
    from betty.typing import Intersection


class DataDefinition[
    DataT,
    StageT: Stage = ClsDefinitionCapabilityStage,
    PorterT: Porter = Porter,
    IndexerT: Indexer = Indexer,
](
    HumanFacingDefinition[StageT | ClsDefinitionCapabilityStage],
    OptionalClsDefinition[DataT, StageT],
):
    """
    A data definition.
    """

    def __init__(
        self,
        *args: Any,
        cls: type[DataT] | None = None,
        label: ResolvableLocalizable,
        capabilities: Mapping[
            str,
            tuple[
                type,
                ResolvableStagedCapability[
                    Self, Any, StageT | ClsDefinitionCapabilityStage
                ],
            ],
        ] = _empty_frozen_mapping,
        description: ResolvableLocalizable | None = None,
        porter: ResolvableStagedCapability[
            Self,
            Intersection[PorterT, Porter[DataT]],
            StageT | ClsDefinitionCapabilityStage,
        ]
        | None = None,
        indexer: ResolvableStagedCapability[
            Self,
            Intersection[IndexerT, Indexer[DataT]],
            StageT | ClsDefinitionCapabilityStage,
        ]
        | None = None,
        samples: Iterable[
            Callable[[], Sample[DataT]]
            | Samples[DataT]
            | type[Intersection[DataT, Samplable]]
        ] = (),
        **kwargs: Any,
    ):
        self.__samples = tuple(samples)
        super().__init__(
            *args,
            cls=cls,
            label=label,
            description=description,
            capabilities={
                **capabilities,
                "indexer": (Indexer, indexer),
                "porter": (Porter, porter),
            },
            **kwargs,
        )

    @final
    @property
    def porter(self) -> Intersection[PorterT, Porter[DataT]]:
        """
        The porter for the data.
        """
        return self.capability("porter")

    @final
    @property
    def try_porter(self) -> Intersection[PorterT, Porter[DataT]] | None:
        """
        The porter for the data, if it has one.
        """
        return self.try_capability("porter")

    @final
    @property
    def indexer(self) -> IndexerT:
        """
        The search indexer for the data.
        """
        return self.capability("indexer")

    @final
    @property
    def try_indexer(self) -> IndexerT | None:
        """
        The search indexer for the data, if it has one.
        """
        return self.try_capability("indexer")

    @override
    def _set_cls(self, cls: type[DataT], /) -> None:
        if issubclass(cls, Data):
            assert cls not in _datas, (
                f"Found an existing data definition {_datas[cls]} when adding {self} for {cls}"
            )
            _datas[cls] = self
        super()._set_cls(cls)

    @final
    @property
    def samples(self) -> Samples:
        """
        Any samples for this data.
        """
        if not self.__samples:
            if self.cls and issubclass(self.cls, Samplable):
                return Samples([self.cls])
            return Samples(())
        return Samples(self.__samples)


_datas: Final[MutableMapping[type, DataDefinition]] = {}


class Data[DataDefinitionT: DataDefinition = DataDefinition]:
    """
    A class that defines data for its instances.
    """

    __slots__ = ()

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
