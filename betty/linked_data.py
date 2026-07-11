"""
Provide `JSON-LD <https://json-ld.org/>`_ utilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, final

from betty.typing import Void, VoidableType

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping

    from betty.portable import PortableData, PortableMapping
    from betty.project import Project
    from betty.typing import VoidType


@final
@dataclass(frozen=True)
class LinkedData:
    """
    Linked data.
    """

    data: PortableData
    context: str | None = field(default=None)


class LinkedDataPortable(ABC):
    """
    An object that can be dumped to linked data.
    """

    @classmethod
    @abstractmethod
    async def linked_data_schema(
        cls, project: Project, /
    ) -> VoidableType[PortableMapping]:
        """
        Define the `JSON Schema <https://json-schema.org/>`_ for :py:meth:`betty.linked_data.LinkedDataPortable.dump_linked_data`.
        """

    @abstractmethod
    async def dump_linked_data(self, project: Project, /) -> LinkedData | VoidType:
        """
        Dump this instance to `JSON-LD <https://json-ld.org/>`_.
        """


class LinkedDataPorter[T](ABC):
    """
    Provide linked data for instances of a target type.
    """

    @abstractmethod
    async def schema(self, project: Project, /) -> VoidableType[PortableMapping]:
        """
        Define the `JSON Schema <https://json-schema.org/>`_ for :py:meth:`betty.linked_data.LinkedDataPorter.dump`.
        """

    @abstractmethod
    async def dump(self, project: Project, data: T, /) -> LinkedData | VoidType:
        """
        Dump the given target to `JSON-LD <https://json-ld.org/>`_.
        """


def embed_linked_data(
    key: str, data: LinkedData | VoidType, *, contexts: MutableMapping[str, str]
) -> Mapping[str, PortableData]:
    """
    Embed linked data into another.
    """
    if data is Void:
        return {}
    if data.context:
        contexts[key] = data.context
    return {
        key: data.data,
    }


def embed_linked_datas(
    datas: Mapping[str, LinkedData | VoidType], /, contexts: MutableMapping[str, str]
) -> Mapping[str, PortableData]:
    """
    Embed multiple pieces of linked data into another.
    """
    linked_data = {}
    for key, data in datas.items():
        linked_data.update(embed_linked_data(key, data, contexts=contexts))
    return linked_data
