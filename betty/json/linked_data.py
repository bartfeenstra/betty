"""
Provide `JSON-LD <https://json-ld.org/>`_ utilities.
"""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import TYPE_CHECKING, cast

from betty.json.schema import Schema
from betty.serde.dump import DumpMapping, Dump

if TYPE_CHECKING:
    from betty.project import Project
    from collections.abc import Sequence
    from betty.ancestry import Link


class LinkedDataDumpable:
    """
    Describe an object that can be dumped to linked data.
    """

    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        """
        Dump this instance to `JSON-LD <https://json-ld.org/>`_.
        """
        return {}

    @classmethod
    async def linked_data_schema(cls, project: Project) -> Schema:
        """
        Define the `JSON Schema <https://json-schema.org/>`_ for :py:meth:`betty.json.linked_data.LinkedDataDumpable.dump_linked_data`.
        """
        return Schema()


def dump_context(dump: DumpMapping[Dump], **contexts: str | Sequence[str]) -> None:
    """
    Add one or more contexts to a dump.
    """
    context_dump = cast(DumpMapping[Dump], dump.setdefault("@context", {}))
    for key, schema_org in contexts.items():
        context_dump[key] = f"https://schema.org/{schema_org}"


async def dump_link(dump: DumpMapping[Dump], project: Project, *links: Link) -> None:
    """
    Add one or more links to a dump.
    """
    link_dump = cast(MutableSequence[DumpMapping[Dump]], dump.setdefault("links", []))
    for link in links:
        link_dump.append(await link.dump_linked_data(project))


class JsonLdSchema(Schema):
    """
    A `JSON-LD <https://json-ld.org/>`_ Json Schema.
    """

    def __init__(self):
        super().__init__(
            name="jsonLd",
            schema={
                "description": "A JSON-LD annotation.",
            },
        )


def add_json_ld(into: Schema) -> None:
    """
    Allow `JSON-LD <https://json-ld.org/>`_ properties to be added to a schema.
    """
    cast(DumpMapping[Dump], into.schema.setdefault("patternProperties", {}))["^@"] = (
        JsonLdSchema().embed(into)
    )
