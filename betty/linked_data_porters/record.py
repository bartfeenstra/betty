"""
Porters for record data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.data import Data
from betty.datas.aggregate.record import RecordDefinition
from betty.json_schema import embed_json_schema
from betty.linked_data import LinkedData, LinkedDataPorter, embed_linked_datas
from betty.media_types.json_ld import JSON_LD
from betty.string import snake_case_to_lower_camel_case
from betty.typing import Voidable, VoidType

if TYPE_CHECKING:
    from betty.portable import PortableMapping
    from betty.project import Project


@final
class RecordLinkedDataPorter[DataClsT: Data[RecordDefinition]](
    LinkedDataPorter[DataClsT]
):
    """
    Port record data to linked data.
    """

    def __init__(
        self,
        data: RecordDefinition,
        /,
        *,
        type: str = "https://schema.org/Thing",  # noqa: A002
    ):
        self._data = data
        self._type = type

    @override
    async def schema(self, project: Project, /) -> PortableMapping:
        defs = {}
        properties = {}
        required = []
        property_schemas = {
            snake_case_to_lower_camel_case(
                field_name.element
            ): await field.data.linked_data_porter.schema(project)
            for field_name, field in self._data.fields.items()
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
        # def_name = f"{kebab_case_to_lower_camel_case(cls.plugin().id)}Entity"
        return {
            # "$ref": f"#/$defs/{def_name}",
            # "$defs": {
            #     **defs,
            #     def_name: {
            #         "additionalProperties": False,
            #         "properties": {
            #             **properties,
            #             "id": {
            #                 "title": "Entity ID",
            #                 "type": "string",
            #             },
            #         },
            #         "required": [*required, "id"],
            #         "type": "object",
            #     },
            # },
        }

    @override
    async def dump(self, project: Project, data: DataClsT, /) -> LinkedData | VoidType:
        url_generator = await project.url_generator
        contexts = {}
        return LinkedData({
            **embed_linked_datas(
                {
                    snake_case_to_lower_camel_case(
                        field_name.element
                    ): await field.data.linked_data_porter.dump(
                        project, field_name.get(data)
                    )
                    for field_name, field in self._data.fields.items()
                },
                contexts=contexts,
            ),
            "@id": url_generator.generate(self, media_type=JSON_LD, absolute=True),
            "@type": self._type,
            "@context": contexts,
            "id": self.id,
        })
