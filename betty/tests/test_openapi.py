from typing import Sequence

import pytest
from betty.app import App
from betty.json.schema import Schema
from betty.openapi import Specification, SpecificationSchema
from betty.project import Project
from betty.serde.dump import Dump
from betty.test_utils.json.schema import SchemaTestBase
from typing_extensions import override


class TestSpecification:
    @pytest.mark.parametrize(
        "clean_urls",
        [
            True,
            False,
        ],
    )
    async def test_build(self, clean_urls: bool, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.clean_urls = clean_urls
            async with project:
                sut = Specification(project)
                specification = await sut.build()
        schema = await SpecificationSchema.new()
        schema.validate(specification)


class TestSpecificationSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        return [
            (await SpecificationSchema.new(), [], []),
        ]
