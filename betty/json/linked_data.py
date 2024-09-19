"""
Provide `JSON-LD <https://json-ld.org/>`_ utilities.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import MutableSequence
from pathlib import Path
from typing import TYPE_CHECKING, cast, Self, Generic, TypeVar

from betty.asyncio import wait_to_thread
from betty.json.schema import FileBasedSchema, Schema, Object
from betty.serde.dump import DumpMapping, Dump

if TYPE_CHECKING:
    from betty.project import Project
    from betty.ancestry.link import Link


_SchemaTypeT = TypeVar("_SchemaTypeT", bound=Schema, covariant=True)


class LinkedDataDumpable(Generic[_SchemaTypeT]):
    """
    Describe an object that can be dumped to linked data.
    """

    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        """
        Dump this instance to `JSON-LD <https://json-ld.org/>`_.
        """
        from betty.project import ProjectSchema

        dump: DumpMapping[Dump] = {}
        schema = await self.linked_data_schema(project)
        if schema.def_name:
            dump["$schema"] = ProjectSchema.def_url(project, schema.def_name)
        return dump

    @classmethod
    @abstractmethod
    async def linked_data_schema(cls, project: Project) -> _SchemaTypeT:
        """
        Define the `JSON Schema <https://json-schema.org/>`_ for :py:meth:`betty.json.linked_data.LinkedDataDumpable.dump_linked_data`.
        """
        pass


def dump_context(dump: DumpMapping[Dump], **context_definitions: str) -> None:
    """
    Add one or more contexts to a dump.
    """
    context_dump = cast(DumpMapping[Dump], dump.setdefault("@context", {}))
    for key, context_definition in context_definitions.items():
        context_dump[key] = context_definition


async def dump_link(dump: DumpMapping[Dump], project: Project, *links: Link) -> None:
    """
    Add one or more links to a dump.
    """
    link_dump = cast(MutableSequence[DumpMapping[Dump]], dump.setdefault("links", []))
    for link in links:
        link_dump.append(await link.dump_linked_data(project))


class JsonLdSchema(FileBasedSchema):
    """
    A `JSON-LD <https://json-ld.org/>`_ JSON Schema reference.
    """

    @classmethod
    async def new(cls) -> Self:
        """
        Create a new instance.
        """
        return await cls.new_for(
            Path(__file__).parent / "schemas" / "json-ld.json",
            def_name="jsonLd",
            title="JSON-LD",
        )


class JsonLdObject(Object):
    """
    A JSON Schema for an object with JSON-LD.
    """

    def __init__(
        self,
        *,
        def_name: str | None = None,
        title: str | None = None,
        description: str | None = None,
    ):
        super().__init__(
            def_name=def_name,
            title=title,
            description=description,
        )
        self._schema["allOf"] = [wait_to_thread(JsonLdSchema.new()).embed(self)]
