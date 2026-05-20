"""
The portable data API.

Portable data can easily be persistent or transmitted across and between systems.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, MutableMapping, MutableSequence
from typing import Self, final, override

type PortableData = (
    bool
    | int
    | float
    | str
    | None
    | MutableSequence[PortableData]
    | MutableMapping[str, PortableData]
)
"""
Portable data.

Data of this type is portable and can easily be persisted or transmitted.
"""


type PortableSequence[PortableDataT: PortableData] = MutableSequence[PortableDataT]
"""
A sequence of portable data.
"""


type PortableMapping[PortableDataT: PortableData] = MutableMapping[str, PortableDataT]
"""
A key-value mapping of portable data.

Keys are strings.
"""


class Portable[PortableDataT: PortableData](ABC):
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
    def dump(self) -> PortableDataT:
        """
        Dump the instance to portable data.

        :raises betty.portable.error.NotPortable: Raised if any part of the data is not portable.
        """


class Porter[DataClsT, PortableDataT: PortableData = PortableData](ABC):
    """
    An object capable of dumping and loading data to and from portable data.
    """

    @abstractmethod
    def load(self, portable: PortableData, /) -> DataClsT:
        """
        Load data from its portable form.
        """

    @abstractmethod
    def dump(self, data: DataClsT, /) -> PortableDataT:
        """
        Dump data to its portable form.
        """

    def copy(self, data: DataClsT) -> DataClsT:
        """
        Deep-copy data into a new instance.
        """
        return self.load(self.dump(data))


@final
class CallbackPorter[DataClsT, PortableDataT: PortableData = PortableData](
    Porter[DataClsT, PortableDataT]
):
    """
    Make data portable using a separate loader and dumper.
    """

    def __init__(
        self,
        loader: Callable[[PortableData], DataClsT],
        dumper: Callable[[DataClsT], PortableDataT],
        /,
    ):
        self._loader = loader
        self._dumper = dumper

    @override
    def load(self, portable: PortableData) -> DataClsT:
        return self._loader(portable)

    @override
    def dump(self, data: DataClsT) -> PortableDataT:
        return self._dumper(data)


class PortablePorter[PortableT: Portable, PortableDataT: PortableData = PortableData](
    Porter[PortableT, PortableDataT]
):
    """
    Expose a portable data type as a porter.
    """

    def __init__(self, cls: type[PortableT]):
        self._cls = cls

    @override
    def load(self, portable: PortableData) -> PortableT:
        return self._cls.load(portable)

    @override
    def dump(self, data: PortableT) -> PortableDataT:
        return data.dump()


@final
class OptionalPorter[PortableT, PortableDataT: PortableData = PortableData](
    Porter[PortableT | None, PortableDataT | None]
):
    """
    Add optional (``None``) support to another porter.
    """

    def __init__(self, proxied: Porter[PortableT, PortableDataT]):
        self._proxied = proxied

    @override
    def load(self, portable: PortableData) -> PortableT | None:
        if portable is None:
            return None
        return self._proxied.load(portable)

    @override
    def dump(self, data: PortableT | None) -> PortableDataT | None:
        if data is None:
            return None
        return self._proxied.dump(data)
