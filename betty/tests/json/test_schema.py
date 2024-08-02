import json as stdjson
from pathlib import Path
from typing import Sequence

import aiofiles
import jsonschema
import pytest
from typing_extensions import override

from betty.app import App
from betty.json.schema import (
    ProjectSchema,
    Schema,
    Ref,
    LocaleSchema,
    JsonSchemaReference,
    ArraySchema,
    JsonSchemaSchema,
)
from betty.project import Project
from betty.serde.dump import Dump
from betty.test_utils.json.schema import SchemaTestBase, DUMMY_SCHEMAS


class TestSchema(SchemaTestBase):
    @override
    async def get_sut_instances(self) -> Sequence[tuple[Schema, Sequence[Dump]]]:
        return DUMMY_SCHEMAS


class TestArraySchema(SchemaTestBase):
    @override
    async def get_sut_instances(self) -> Sequence[tuple[Schema, Sequence[Dump]]]:
        return [
            schema
            for schemas in (
                (
                    (
                        ArraySchema(items_schema),
                        [*[[data] for data in datas], list(datas)],
                    ),
                    (
                        ArraySchema(items_schema, name="myFirstArraySchema"),
                        [*[[data] for data in datas], list(datas)],
                    ),
                )
                for items_schema, datas in DUMMY_SCHEMAS
            )
            for schema in schemas
        ]


class TestRef(SchemaTestBase):
    @override
    async def get_sut_instances(self) -> Sequence[tuple[Schema, Sequence[Dump]]]:
        return [
            (Ref("foo"), []),
            (Ref("bar"), []),
            (Ref("baz"), []),
        ]


class TestLocaleSchema(SchemaTestBase):
    @override
    async def get_sut_instances(self) -> Sequence[tuple[Schema, Sequence[Dump]]]:
        return [(LocaleSchema(), ["en", "nl", "uk"])]


class TestJsonSchemaReference(SchemaTestBase):
    @override
    async def get_sut_instances(self) -> Sequence[tuple[Schema, Sequence[Dump]]]:
        return [(JsonSchemaReference(), [])]


class TestJsonSchemaSchema(SchemaTestBase):
    @override
    async def get_sut_instances(self) -> Sequence[tuple[Schema, Sequence[Dump]]]:
        return [(await JsonSchemaSchema.new(), [])]


class TestProjectSchema(SchemaTestBase):
    @override
    async def get_sut_instances(self) -> Sequence[tuple[Schema, Sequence[Dump]]]:
        schemas = []
        for clean_urls in (True, False):
            async with App.new_temporary() as app, app, Project.new_temporary(
                app
            ) as project:
                project.configuration.clean_urls = clean_urls
                async with project:
                    schemas.append((await ProjectSchema.new(project), ()))
        return schemas

    @pytest.mark.parametrize(
        "clean_urls",
        [
            True,
            False,
        ],
    )
    async def test_new(self, clean_urls: bool, new_temporary_app: App) -> None:
        async with aiofiles.open(
            Path(__file__).parent.parent.parent
            / "test_utils"
            / "json"
            / "json-schema-schema.json"
        ) as f:
            json_schema_schema = stdjson.loads(await f.read())

        async with Project.new_temporary(new_temporary_app) as project, project:
            schema = await ProjectSchema.new(project)
        jsonschema.validate(json_schema_schema, schema.schema)
