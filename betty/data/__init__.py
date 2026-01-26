"""
Describe, access, and manipulate arbitrary data.
"""

from __future__ import annotations

from functools import update_wrapper
from typing import TYPE_CHECKING, Any, Generic, Self

from typing_extensions import TypeVar, override

from betty.data.sample import Sample, Samples
from betty.definition.cls import ClsDefinition
from betty.definition.human_facing import HumanFacingDefinition
from betty.importlib import fully_qualified_name
from betty.portable import Portable, PortableData, PortablePorter, Porter
from betty.portable.error import NotPortable
from betty.service.hydrate import Hydratable, Hydrator

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from ty_extensions import Intersection

    from betty.locale.localizable import LocalizableLike
    from betty.service.level import ServiceLevel

_DataClsT = TypeVar("_DataClsT", default=Any)
_PortableDataCoT = TypeVar(
    "_PortableDataCoT", bound=PortableData, default=PortableData, covariant=True
)


class DataDefinition(
    HumanFacingDefinition,
    ClsDefinition[_DataClsT],
    Hydrator[_DataClsT],
    Generic[_DataClsT, _PortableDataCoT],
):
    """
    A data definition.
    """

    _porter: Porter[_DataClsT, _PortableDataCoT] | None

    def __init__(
        self,
        *,
        cls: type[_DataClsT] | None = None,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
        porter: Porter[_DataClsT, _PortableDataCoT] | None = None,
        fallback_porter: Porter[_DataClsT, _PortableDataCoT] | None = None,
        samples: Iterable[Callable[[], Sample[_DataClsT]]] | None = None,
        empty: Callable[[_DataClsT], bool] | None = None,
    ):
        super().__init__(cls=cls, label=label, description=description)
        self._porter = porter
        self._fallback_porter = fallback_porter
        self._samples = Samples(() if samples is None else samples)
        self._empty = empty

    @property
    def porter(self) -> Porter[_DataClsT, _PortableDataCoT]:
        """
        The porter for the data.
        """
        if self._porter is None:
            if issubclass(self.cls, Portable):
                self._porter = PortablePorter(self.cls)  # ty:ignore[invalid-assignment]
            elif self._fallback_porter is not None:
                self._porter = self._fallback_porter

            else:
                raise NotPortable(
                    f"This definition does not have a porter. Either make the data class {fully_qualified_name(self.cls)} subclass {fully_qualified_name(Portable)}, or provide a porter when initializing the definition."
                )
        assert self._porter is not None
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
    async def hydrate(self, services: ServiceLevel, data: _DataClsT, /) -> None:
        from betty.config import Configuration

        if isinstance(data, Hydratable):
            await data.hydrate(services)
        if isinstance(data, Configuration):
            assert services is not None
            validator = data.validator
            if validator is not None:
                await services.new_target(validator)

    def empty(self, data: _DataClsT, /) -> bool:
        """
        Check if the data can be considered 'empty'.
        """
        if self._empty is None:
            return False
        return self._empty(data)


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
            f"{fully_qualified_name(cls)} was not decorated with a {fully_qualified_name(DataDefinition)} subclass."
        )

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        porter = type(self).data().porter
        return porter.dump(self) == porter.dump(other)
