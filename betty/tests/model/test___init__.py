from typing import Sequence

from betty.model import EntityReferenceSchema, EntityReferenceCollectionSchema
from betty.test_utils.model import DummyEntity
from typing_extensions import override

from betty.json.schema import Schema
from betty.serde.dump import Dump
from betty.test_utils.json.schema import SchemaTestBase


class TestEntityReferenceSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                EntityReferenceSchema(DummyEntity),
                [
                    "https://example.com",
                ],
                [True, False, None, 123, [], {}],
            ),
        ]


class TestEntityReferenceCollectionSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (
                EntityReferenceCollectionSchema(DummyEntity),
                [
                    [],
                    ["https://example.com"],
                ],
                [True, False, None, "123", 123, {}],
            ),
        ]
