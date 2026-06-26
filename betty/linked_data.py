"""
Provide `JSON-LD <https://json-ld.org/>`_ utilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, final, override

from betty.attr import HasAttrs
from betty.json_schema import embed_json_schema
from betty.media_types.json_ld import JSON_LD
from betty.string import kebab_case_to_lower_camel_case, snake_case_to_lower_camel_case
from betty.typing import Void, Voidable, VoidableType

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


# @todo refactor this into a linked data porter
# @todo We should center it around RecordDefinition, because we will need to work with FieldDefinition to handle matters
# @todo such as privacy checks.
# @todo
class HasLinkedDataAttrs(LinkedDataPortable, HasAttrs):
    """
    An object that has attributes and can be dumped to linked data.
    """

    @final
    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> PortableMapping:
        defs = {}
        properties = {}
        required = []
        property_schemas = {
            **await cls.linked_data_schema_properties(project),
            **{
                snake_case_to_lower_camel_case(
                    attr.prop.name
                ): await attr.field.data.linked_data_porter.schema(project)
                for attr in cls.attrs()
            },
        }
        for property_name, property_schema in property_schemas.items():
            if isinstance(property_schema, Voidable):
                _property_schema = property_schema.wrapped
            else:
                _property_schema = property_schema
                required.append(property_name)
            properties[property_name] = embed_json_schema(_property_schema, defs=defs)
        # @todo For the @type as well as the def name, add two (class?) methods.
        # @todo Override the def name method in Entity.
        # @todo
        # @todo ACTUALLY.... Can we reuse dump_linked_data_properties() for this?
        # @todo
        # @todo
        # @todo
        def_name = f"{kebab_case_to_lower_camel_case(cls.plugin().id)}Entity"
        return {
            "$ref": f"#/$defs/{def_name}",
            "$defs": {
                **defs,
                def_name: {
                    "additionalProperties": False,
                    "properties": {
                        **properties,
                        "id": {
                            "title": "Entity ID",
                            "type": "string",
                        },
                    },
                    "required": [*required, "id"],
                    "type": "object",
                },
            },
        }

    @classmethod
    async def linked_data_schema_properties(
        cls, project: Project, /
    ) -> Mapping[str, VoidableType[PortableMapping]]:
        """
        Define additional properties for the linked data schema.
        """
        return {}

    @final
    @override
    async def dump_linked_data(self, project: Project, /) -> LinkedData:
        url_generator = await project.url_generator
        contexts = {}
        return LinkedData({
            **embed_linked_datas(
                await self.dump_linked_data_properties(project),
                {
                    snake_case_to_lower_camel_case(
                        attr.prop.name
                    ): await attr.field.data.linked_data_porter.dump(
                        project, attr.get(self)
                    )
                    for attr in self.attrs()
                },
                contexts=contexts,
            ),
            "@id": url_generator.generate(self, media_type=JSON_LD, absolute=True),
            "@type": self._linked_data_type,
            "@context": contexts,
            "id": self.id,
        })

    async def dump_linked_data_properties(
        self, project: Project, /
    ) -> Mapping[str, LinkedData | VoidType]:
        """
        Dump additional properties to linked data.
        """
        return {}


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
    *data_sets: Mapping[str, LinkedData | VoidType], contexts: MutableMapping[str, str]
) -> Mapping[str, PortableData]:
    """
    Embed multiple pieces of linked data into another.
    """
    linked_data = {}
    for data_set in data_sets:
        for key, data in data_set.items():
            linked_data.update(embed_linked_data(key, data, contexts=contexts))
    return linked_data
