"""
Describe, access, and manipulate arbitrary data.
"""

from __future__ import annotations

from functools import update_wrapper
from typing import TYPE_CHECKING, Self, override

from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.importlib import fully_qualified_name
from betty.portable import Portable, PortableData, PortablePorter, Porter
from betty.portable.error import NotPortable
from betty.sample import Samplable, Sample, Samples

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from betty.locale.localizable import ResolvableLocalizable
    from betty.typing import Intersection


class DataDefinition[DataClsT, PortableDataT: PortableData = PortableData](
    HumanFacingDefinition, ClsDefinition[DataClsT]
):
    """
    A data definition.
    """

    def __init__(
        self,
        /,
        cls: type[DataClsT] | None = None,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        porter: Porter[DataClsT, PortableDataT] | None = None,
        samples: Iterable[
            Callable[[], Sample[DataClsT]]
            | Samples[DataClsT]
            | type[Intersection[DataClsT, Samplable]]
        ] = (),
    ):
        super().__init__(cls=cls, label=label, description=description)
        self._porter = porter
        self._samples = tuple(samples)

    @property
    def porter(self) -> Porter[DataClsT, PortableDataT]:
        """
        The porter for the data.
        """
        if self._porter is None:
            if not issubclass(self.cls, Portable):
                raise NotPortable(
                    f"This definition does not have a porter. Either make the data class {fully_qualified_name(self.cls)} subclass {fully_qualified_name(Portable)}, or provide a porter when initializing the definition."
                )
            self._porter = PortablePorter(self.cls)
        return self._porter  # ty:ignore[invalid-return-type]

    @override
    def _set_cls(self, cls: type[DataClsT], /) -> None:
        super()._set_cls(cls)
        if issubclass(cls, Data):
            cls.data = staticmethod(update_wrapper(lambda: self, cls.data))  # ty:ignore[invalid-assignment]

    @property
    def samples(self) -> Samples:
        """
        Any samples for this data.
        """
        if not self._samples:
            if issubclass(self.cls, Samplable):
                return Samples([self.cls])
            return Samples(())
        return Samples(self._samples)


class Data[DataDefinitionT: DataDefinition = DataDefinition]:
    """
    A class that defines data for its instances.
    """

    @classmethod
    def data(cls) -> Intersection[DataDefinitionT, DataDefinition[Self]]:
        """
        Define the data for instances of this class.
        """
        raise NotImplementedError(
            f"{fully_qualified_name(cls)} was not decorated with {fully_qualified_name(DataDefinition)} or any subclass."
        )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        porter = type(self).data().porter
        return porter.dump(self) == porter.dump(other)


type ResolvableDataDefinition[DataDefinitionT: DataDefinition] = (
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
