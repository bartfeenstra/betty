"""
Provide `JSON-LD <https://json-ld.org/>`_ utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.serde.dump import DumpMapping, Dump, dump_default

if TYPE_CHECKING:
    from betty.project import Project
    from collections.abc import Sequence
    from betty.model.ancestry import Link


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
    async def linked_data_schema(cls, project: Project) -> DumpMapping[Dump]:
        """
        Define the `JSON Schema <https://json-schema.org/>`_ for :py:meth:`betty.json.linked_data.LinkedDataDumpable.dump_linked_data`.
        """
        return {}


def dump_context(dump: DumpMapping[Dump], **contexts: str | Sequence[str]) -> None:
    """
    Add one or more contexts to a dump.
    """
    context_dump = dump_default(dump, "@context", dict)
    for key, schema_org in contexts.items():
        context_dump[key] = f"https://schema.org/{schema_org}"


async def dump_link(dump: DumpMapping[Dump], project: Project, *links: Link) -> None:
    """
    Add one or more links to a dump.
    """
    link_dump = dump_default(dump, "links", list)
    for link in links:
        link_dump.append(await link.dump_linked_data(project))


def ref_json_ld(root_schema: DumpMapping[Dump]) -> DumpMapping[Dump]:
    """
    Reference the `JSON-LD <https://json-ld.org/>`_ schema.
    """
    definitions = dump_default(root_schema, "definitions", dict)
    if "jsonLd" not in definitions:
        definitions["jsonLd"] = {
            "description": "A JSON-LD annotation.",
        }
    return {
        "$ref": "#/definitions/jsonLd",
    }


def add_json_ld(
    schema: DumpMapping[Dump], root_schema: DumpMapping[Dump] | None = None
) -> None:
    """
    Allow `JSON-LD <https://json-ld.org/>`_ properties to be added to a schema.
    """
    schema["patternProperties"] = {
        "^@": ref_json_ld(root_schema or schema),
    }
