import pytest

from betty.json_schemas.openapi import OpenapiSchema
from betty.openapi import Specification
from betty.test_utils.conftest import NewIsolatedProject


class TestSpecification:
    @pytest.mark.parametrize(
        "clean_urls",
        [
            True,
            False,
        ],
    )
    async def test_build(
        self, clean_urls: bool, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with new_isolated_project() as project:
            project.clean_urls = True
            async with project:
                sut = Specification(project)
                specification = await sut.build()
            OpenapiSchema().validate(specification)
