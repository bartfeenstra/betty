"""
The portable data API.

Portable data can easily be persistent or transmitted across and between systems.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, MutableMapping, MutableSequence
from typing import Generic, Self, TypeAlias, final, override

from typing_extensions import TypeVar

_DataClsT = TypeVar("_DataClsT")


PortableData: TypeAlias = (
    bool
    | int
    | float
    | str
    | None
    | MutableSequence["PortableData"]
    | MutableMapping[str, "PortableData"]
)
"""
Portable data.

Data of this type is portable and can easily be persisted or transmitted.
"""


_PortableDataT = TypeVar("_PortableDataT", bound=PortableData, default=PortableData)


PortableSequence: TypeAlias = MutableSequence[_PortableDataT]
"""
A sequence of portable data.
"""


PortableMapping: TypeAlias = MutableMapping[str, _PortableDataT]
"""
A key-value mapping of portable data.

Keys are strings.
"""


class Portable(ABC, Generic[_PortableDataT]):
    """
    A class that can be dumped to and loaded from portable data.
    """

    @classmethod
    @abstractmethod
    def load(cls, portable: PortableData, /) -> Self:
        """
        Create a new instance from portable data.

        :raises betty.exception.HumanFacingException: Raised if the portable data is invalid.
        """

    @abstractmethod
    def dump(self) -> _PortableDataT:
        """
        Dump the instance to portable data.

        :raises betty.portable.error.NotPortable: Raised if any part of the data is not portable.
        """


_PortableT = TypeVar("_PortableT", bound=Portable)


class Porter(ABC, Generic[_DataClsT, _PortableDataT]):
    """
    An object capable of dumping and loading data to and from portable data.
    """

    @abstractmethod
    def load(self, portable: PortableData, /) -> _DataClsT:
        """
        Load data from its portable form.
        """

    @abstractmethod
    def dump(self, data: _DataClsT, /) -> _PortableDataT:
        """
        Dump data to its portable form.
        """

    def copy(self, data: _DataClsT) -> _DataClsT:
        """
        Deep-copy data into a new instance.
        """
        return self.load(self.dump(data))


@final
class CallbackPorter(Porter[_DataClsT, _PortableDataT]):
    """
    Make data portable using a separate loader and dumper.
    """

    def __init__(
        self,
        loader: Callable[[PortableData], _DataClsT],
        dumper: Callable[[_DataClsT], _PortableDataT],
        /,
    ):
        self._loader = loader
        self._dumper = dumper

    @override
    def load(self, portable: PortableData) -> _DataClsT:
        return self._loader(portable)

    @override
    def dump(self, data: _DataClsT) -> _PortableDataT:
        return self._dumper(data)


class PortablePorter(Porter[_PortableT, _PortableDataT]):
    """
    Expose a portable data type as a porter.
    """

    def __init__(self, cls: type[_PortableT]):
        self._cls = cls

    @override
    def load(self, portable: PortableData) -> _PortableT:
        return self._cls.load(portable)

    @override
    def dump(self, data: _PortableT) -> _PortableDataT:
        return data.dump()  # ty:ignore[invalid-return-type]


@final
class OptionalPorter(
    Porter[_PortableT | None, _PortableDataT | None],
    Generic[_PortableT, _PortableDataT],
):
    """
    Add optional (``None``) support to another porter.
    """

    def __init__(self, upstream: Porter[_PortableT, _PortableDataT]):
        self._upstream = upstream

    @override
    def load(self, portable: PortableData) -> _PortableT | None:
        if portable is None:
            return None
        return self._upstream.load(portable)

    @override
    def dump(self, data: _PortableT | None) -> _PortableDataT | None:
        if data is None:
            return None
        return self._upstream.dump(data)
