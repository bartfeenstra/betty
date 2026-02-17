"""
Describe, access, and manipulate arbitrary data.
"""

from __future__ import annotations

from functools import update_wrapper
from typing import TYPE_CHECKING, Any, Self, final, override

from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.importlib import fully_qualified_name
from betty.portable import OptionalPorter, Portable, PortablePorter, Porter
from betty.portable.error import NotPortable
from betty.sample import Samplable, Sample, Samples, Size

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from ty_extensions import Intersection

    from betty.locale.localizable import ResolvableLocalizable


class DataDefinition[DataClsT](HumanFacingDefinition, ClsDefinition[DataClsT]):
    """
    A data definition.
    """

    def __init__(
        self,
        *,
        cls: type[DataClsT] | None = None,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        porter: Porter[DataClsT] | None = None,
        samples: Iterable[
            Callable[[], Sample[DataClsT]]
            | Samples[DataClsT]
            | type[Intersection[DataClsT, Samplable]]
        ]
        | None = None,
    ):
        super().__init__(cls=cls, label=label, description=description)
        self._porter = porter
        self._samples = samples

    @property
    def porter(self) -> Porter[DataClsT]:
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
    def _set_cls(self, cls: type[DataClsT]) -> None:
        super()._set_cls(cls)
        if issubclass(cls, Data):
            cls.data = staticmethod(update_wrapper(lambda: self, cls.data))  # ty:ignore[invalid-assignment]

    @property
    def samples(self) -> Samples:
        """
        Any samples for this data.
        """
        if self._samples is None:
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

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        porter = type(self).data().porter
        return porter.dump(self) == porter.dump(other)


@final
class OptionalDefinition[DataClsT](DataDefinition[DataClsT | None]):
    """
    Wrap another data definition to make it optional, e.g. allow ``None``.
    """

    def __init__(self, wrapped: DataDefinition[DataClsT], /):
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
    def wrapped(self) -> DataDefinition[DataClsT]:
        """
        The wrapped, required (non-optional) data definition.
        """
        return self._wrapped
