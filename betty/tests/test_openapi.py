import pytest
from typing_extensions import override

from betty.app import App
from betty.openapi import Specification, SpecificationSchema
from betty.project import Project
from betty.test_utils.json.schema import SchemaTestBase, SchemaTestBaseSut


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
        SpecificationSchema().validate(specification)


class TestSpecificationSchema(SchemaTestBase):
    @override
    @pytest.fixture
    def sut(self) -> SchemaTestBaseSut:
        return (SpecificationSchema(), [], [])
