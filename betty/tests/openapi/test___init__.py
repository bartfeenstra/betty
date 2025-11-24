import pytest

from betty.app import App
from betty.openapi import Specification
from betty.openapi.schema import SpecificationSchema
from betty.project import Project


class TestSpecification:
    @pytest.mark.parametrize(
        "clean_urls",
        [
            True,
            False,
        ],
    )
    async def test_build(self, clean_urls: bool, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.clean_urls = clean_urls
            async with project:
                sut = Specification(project)
                specification = await sut.build()
        SpecificationSchema().validate(specification)
