"""
Describe, access, and manipulate arbitrary data.
"""

from __future__ import annotations

from functools import update_wrapper
from typing import TYPE_CHECKING, Any, Generic, Self

from typing_extensions import TypeVar

from betty.importlib import fully_qualified_name
from betty.locale.localizable.ensure import ensure_localizable
from betty.portable import Portable, PortableData, PortablePorter, Porter
from betty.portable.error import NotPortable
from betty.service.hydrate import Hydratable

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from ty_extensions import Intersection

    from betty.locale.localizable import Localizable, LocalizableLike
    from betty.service.level import ServiceLevel

_DataClsT = TypeVar("_DataClsT", default=Any)


class DataDefinition(Generic[_DataClsT]):
    """
    A data definition.
    """

    def __init__(
        self,
        *,
        cls: type[_DataClsT] | None = None,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
        porter: Porter[_DataClsT] | None = None,
        fallback_porter: Porter[_DataClsT] | None = None,
        samples: Iterable[Callable[[], Sample[_DataClsT]]] | None = None,
        empty: Callable[[_DataClsT], bool] | None = None,
    ):
        self._cls: type[_DataClsT] | None = None
        self._label = ensure_localizable(label)
        self._description = (
            None if description is None else ensure_localizable(description)
        )
        self._porter = porter
        self._fallback_porter = fallback_porter
        self._samples = () if samples is None else list(samples)
        self._empty = empty
        if cls is not None:
            self._cls = cls

    @property
    def cls(self) -> type[_DataClsT]:
        """
        The data's Python type.
        """
        if self._cls is None:
            raise ValueError("This definition was not yet used to decorate a class.")
        assert self._cls is not None
        return self._cls

    @property
    def porter(self) -> Porter[_DataClsT]:
        """
        The porter for the data.
        """
        if self._porter is None:
            if issubclass(self.cls, Portable):
                self._porter = PortablePorter(self.cls)
            elif self._fallback_porter is not None:
                self._porter = self._fallback_porter

            else:
                raise NotPortable(
                    f"This definition does not have a porter. Either make the data class {fully_qualified_name(self.cls)} subclass {fully_qualified_name(Portable)}, or provide a porter when initializing the definition."
                )
        assert self._porter is not None
        return self._porter

    def __call__(self, cls: type[_DataClsT]) -> type[_DataClsT]:
        """
        Decorate a data class.

        :raises ValueError: Raised if the definition was already used to decorate a class.
        """
        if self._cls is not None:
            raise ValueError("This definition was already used to decorate a class.")
        if not issubclass(cls, Data):
            raise ValueError(
                f"Can only decorate classes that subclass {fully_qualified_name(Data)}."
            )
        assert self._cls is None
        cls.data = staticmethod(update_wrapper(lambda: self, cls.data))  # ty:ignore[invalid-assignment]
        self._cls = cls
        return cls

    @property
    def label(self) -> Localizable:
        """
        The human-readable data label.
        """
        return self._label

    @property
    def description(self) -> Localizable | None:
        """
        The human-readable long data description.
        """
        return self._description

    @property
    def samples(self) -> Iterable[Sample[_DataClsT]]:
        """
        Any samples for this data.
        """
        for sample in self._samples:
            yield sample()

    def load(self, portable: PortableData, /) -> _DataClsT:
        """
        Create a new data instance from portable.

        :raises betty.exception.HumanFacingException: Raised if the portable data is invalid.
        """
        return self.porter.load(portable)

    def dump(self, data: _DataClsT, /) -> PortableData:
        """
        Dump the data to portable data.
        """
        return self.porter.dump(data)

    async def hydrate(self, data: _DataClsT, services: ServiceLevel, /) -> None:
        """
        Hydrate the data.

        Hydration allows data definitions to require a :py:type:`betty.service.level.ServiceLevel` to perform tasks
        such as validation or enhancing the data using information or functionality from the service level.
        """
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
        data = type(self).data()
        return data.dump(self) == data.dump(other)


class Sample(Generic[_DataClsT]):
    """
    A data sample.

    Samples are useful for generating documentation and tests.
    """

    def __init__(
        self,
        data: _DataClsT,
        *,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
        minimal: bool = False,
        full: bool = False,
    ):
        self._data = data
        self._label = ensure_localizable(label)
        self._description = ensure_localizable(description) if description else None
        self._minimal = minimal
        self._full = full

    @property
    def data(self) -> _DataClsT:
        """
        The sample data.
        """
        return self._data

    @property
    def label(self) -> Localizable:
        """
        The sample's human-readable short label.
        """
        return self._label

    @property
    def description(self) -> Localizable | None:
        """
        The sample's human-readable long description.
        """
        return self._description

    @property
    def minimal(self) -> bool:
        """
        Whether this is a minimal sample.
        """
        return self._minimal

    @property
    def full(self) -> bool:
        """
        Whether this is a full sample.
        """
        return self._full


class SampleNotFound(Exception):
    """
    Raised when a sample could not be found.
    """
